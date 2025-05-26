import os
import sys
from copy import deepcopy
import math
import time
from collections import Counter
import sudokuimagetool

import gc


import logging
print=logging.info


def getfilenameinfo(fname: str) -> tuple:
    filename = str(fname)
    splitname = filename.split('.')
    ext = splitname[-1]
    actualname = ''.join(splitname[0:-1])
    return (actualname, ext)


def gridstring(grid):
    widest_item_lengths_per_row = [max([len(str(item)) for item in row]) for row in grid] 
    padlen = max(widest_item_lengths_per_row) + 1
    gaplen = round(padlen*1.1)
    gridstr = ''
    for row_i, row in enumerate(grid):
        for col_j, item_ in enumerate(row):
            item = str(item_)
            gridstr += item
            gridstr += str(' ' * (padlen - len(item)))
            if col_j == 8:
                continue
            if (col_j % 3) == 2:
                gridstr += str(' ' * (gaplen))
        if (row_i % 3) == 2:
            gridstr += str('\n\n')
        gridstr += str('\n')
    return gridstr


def gridprint(grid):
    gridstr = gridstring(grid)
    print(gridstr)


def colored(text, color):
    # This is quick and dirty lol
    return text


def breakdowntoset(smalllistorstr):
    largerset = set()
    if isinstance(smalllistorstr, str):
        input = str(smalllistorstr).strip().lower()
    else:
        input = smalllistorstr
    if input == '' or input == []:
        return largerset
    for _ in input:
        if isinstance(_, int):
            largerset.add(_)
        elif _ == '-':
            continue
        elif isinstance(_, bool):
            raise Exception("Somehow a boolean array is passed to be broken into a set")
        else:
            try:
                largerset = largerset | (set(map(int, _.split('-'))))
            except ValueError:
                raise Exception(f"Somehow something that's not a bool, int, or number str, is passed to be broken into a set:\nItem: ({_}), Type: ({type(_)})")
    return largerset


class SolutionsNotUniqueException(Exception):
    pass


class TooManySolutionsException(SolutionsNotUniqueException):
    pass


global EMPTYGRID
EMPTYGRID = list([[0 for _ in range(9)] for _ in range(9)])



class Solver():
    def __init__(self, grid: list):
        global EMPTYGRID
        # CONSTANTS
        self.ALL = set(range(1, 10))
        self.CHECK_CELLS = [(0, 0), (1, 3), (2, 6), (3, 1), (4, 4), (5, 7), (6, 2), (7, 5), (8, 8)]
        # Definitely mathematically reduntant and can be reduced.
        # I don't want to do that though, too lazy. Deal with it, it's not slow enough to care about.
        self.GRID = deepcopy(EMPTYGRID)
        self.SOLUTIONS = []
        self.COUNT = 0
        self.grid = grid
        self.first_grid = deepcopy(grid)


    def SolveByGrid(self, inputgrid) -> tuple:  # takes a base grid and tries to solve for lonely items. returns a candidate-filled kinda-solved grid and the normal kinda-solved grid
        grid = deepcopy(inputgrid)
        candid = deepcopy(grid)
        for i, row in enumerate(grid):
            for j, item in enumerate(row):
                if item == 0:
                    temp_ = row
                    neighbours = deepcopy(temp_)
                    temp_ = [_r[j] for _r in grid]
                    neighbours.extend(temp_)
                    box_i = i // 3
                    box_j = j // 3
                    temp_ = []
                    for i_, row_ in enumerate(grid[box_i*3:(box_i+1)*3]):
                        for j_, item_ in enumerate(row_[box_j*3:(box_j+1)*3]):
                            temp_.append(item_)
                    neighbours.extend(temp_)
                    neighbours = set(neighbours)
                    neighbours.remove(0)
                    possible = self.ALL - neighbours
                    if len(possible) == 1:
                        grid[i][j] = next(iter(possible))
                        candid[i][j] = next(iter(possible))
                    elif len(possible) > 1:
                        candid[i][j] = '-'.join([str(i) for i in iter(possible)])
        return (candid, grid)


    def SolveByCandid(inputcandids, inputgrid) -> list:  # takes a candidate-containing grid and the normal grid and tries to solve based on being the only candidate for a number in a set. returns a kinda-solved normal grid
        candid = deepcopy(inputcandids)
        grid = deepcopy(inputgrid)
        for i, row in enumerate(candid):
            for j, item in enumerate(row):
                if not isinstance(item, int):
                    itemsuperpos = set(map(int, item.split('-')))  # Never used, but I'm too afraid to remove this.
                    neighbour_row = [k for (_, k) in enumerate(row) if (_ != j)]
                    n_r = breakdowntoset(neighbour_row)
                    neighbour_col = [r_[j] for (k, r_) in enumerate(candid) if (k != i) ]
                    n_c = breakdowntoset(neighbour_col)
                    box = []
                    box_i = i // 3
                    box_j = j // 3
                    for i_, row_ in enumerate(candid[box_i*3:(box_i+1)*3]):
                        for j_, item_ in enumerate(row_[box_j*3:(box_j+1)*3]):
                            if i_ == (i % 3) and j_ == (j % 3):
                                continue
                            box.append(item_)
                    n_b = breakdowntoset(box)
                    # THIS OPERATION IS NOT GLOBAL
                    # IT APPLIES SEPERATELY TO EACH LOCK
                    #   What did I mean by this when I added it when first writing this?? I genuinly don't know...
                    r_r = self.ALL - n_r
                    r_c = self.ALL - n_c
                    r_b = self.ALL - n_b
                    if len(r_r) == 1:
                        grid[i][j] = next(iter(r_r))
                    if len(r_c) == 1:
                        grid[i][j] = next(iter(r_c))
                    if len(r_b) == 1:
                        grid[i][j] = next(iter(r_b))
        return grid


    def SimpleSolve(inputgrid) -> tuple:  # takes a normal unsolved grid, and tries to solve it using the two functions above. returns a potentially condidate-containing grid and a potentially solved grid.
        grid = deepcopy(inputgrid)
        candid = deepcopy(grid)
        copygrid = deepcopy(EMPTYGRID)
        copycandid = deepcopy(EMPTYGRID)
        copytotal = deepcopy(EMPTYGRID)
        firsttotal = True
        firstgrid = True
        firstcandid = True
        while copytotal != grid or firsttotal:
            firsttotal = False
            copytotal = deepcopy(grid)
            while copygrid != grid or firstgrid:
                firstgrid = False
                copygrid = deepcopy(grid)
                candid, grid = self.SolveByGrid(grid)
            # runs until SolveByGrid doesn't change grid
            while copycandid != grid or firstcandid:
                firstcandid = False
                copycandid = deepcopy(grid)
                grid = self.SolveByCandid(candid, grid)
            # runs until SolveByCandid doesn't change grid
            candid, grid = self.SolveByGrid(grid)
            # this last step is to generate the candid grid
        return (candid, grid)


    # solves the grid by trying the simple solve methods on it,
    #   "SimpleSolve" method: 
    #     1.single possibility tiles become just that possibility, 
    #     2.if a number can only be in once space of a row/coloumn/box, then that tile becomes the number it can only be there.  
    # then applying a brute force technique to any unsolved tiles and then trying itself again. 
    # takes an unsolved grid as input and returns a boolean for it was solvable alongside a hopefully solved grid.
    def OLD_GuessworkSolve(self, gridbase, debug=False) -> tuple:  
        candid, grid = self.SimpleSolve(gridbase)
        if not self.CheckValidGrid(grid):
            return (False, grid)
        if debug:
            print(colored("[#] Debug turn:\n", "light_yellow"))
            gridprint(candid)
            print("")
        for i, row in enumerate(grid):
            for j, item in enumerate(row):
                if item != 0:
                    continue
                candidatestr = candid[i][j]
                # If a set is of length less than one, then SimpleSolve doesn't assign it a candidate string in the candidates, leaving it as 0.
                if not isinstance(candidatestr, str):
                    if debug:
                        print(colored("[#] *BEEP*! Reached a wrong answer, sorry!", "magenta"))
                    return (False, deepcopy(grid))
                candidates = breakdowntoset(candidatestr)
                
                for r_ in candid:  # Prevent the code from going down a spiral when already a grid is definitely unsolvable.
                    # the impossibility check is to check if anyone is candid grid is 0, which means unsolvable.
                    for j_ in r_:
                        if j_ == 0:
                            return (False, deepcopy(grid))

                candidates = list(candidates)
                candidates.sort()
                # if reaching this point:
                # a number on the grid is missing, and it has possible values as ints in an ordered list from small to large.
                for p in candidates:
                    testgrid = []
                    testgrid = deepcopy(grid)
                    testgrid[i][j] = p
                    couldbesolved, answer = self.OLD_GuessworkSolve(testgrid, debug=debug)
                    if couldbesolved and self.CheckValidGrid(answer):
                        return (True, answer)
                # it's impossible for it not to be one of the values that are possible for a number, so if reaching this point, automatically assume failure.
                if debug:
                    print(colored("[#] Assuming failure.", "magenta"))
                return (False, deepcopy(grid))
        # by this point:
        # the grid must already be solved, not be wrong, not have any emptiness if it's not returned yet.
        # so it'll always return True on checkValidgrid because of the first few lines of this function doing that.
        # return (CheckValidGrid(grid), deepcopy(grid))
        return (True, deepcopy(grid))


    def GuessworkSolve(self) -> tuple:
        if self.SOLUTIONS != []:
            return (True, self.SOLUTIONS[0])
        # else:
        self.CountSolve(self.grid)
        if self.SOLUTIONS != []:
            return (True, self.SOLUTIONS[0])
        # else:
        print(' im so sad, there aint a solution! \n\n\n\n\n  I SAID IM SADDDDDDD!!!')
        status, result = self.OLD_GuessworkSolve(self.first_grid)
        print(status, result)
        return (status, result)


    def CountSolve(self, inputgrid) -> tuple:  
        candid, grid = self.SimpleSolve(inputgrid)
        if not self.CheckValidGrid(grid):
            return (False, grid)
        for i, row in enumerate(grid):
            for j, item in enumerate(row):
                if item != 0:
                    continue
                candidatestr = candid[i][j]
                if not isinstance(candidatestr, str):
                    return (False, deepcopy(grid))
                candidates = breakdowntoset(candidatestr)
                for r_ in candid:
                    for j_ in r_:
                        if j_ == 0:
                            return (False, deepcopy(grid))
                candidates = list(candidates)
                candidates.sort()
                for p in candidates:
                    testgrid = []
                    testgrid = deepcopy(grid)
                    testgrid[i][j] = p
                    couldbesolved, answer = self.CountSolve(testgrid)
                    if couldbesolved and self.CheckValidGrid(answer):
                        # return (True, answer)
                        expanded_answer = []
                        for row in answer:
                            expanded_answer.extend(row)
                        if not (expanded_answer in self.solutions):
                            self.SOLUTIONS.append(deepcopy(expanded_answer))
                            self.COUNT += 1
                            if self.COUNT > 100:
                                raise TooManySolutionsException("Too many solutions! I counted at least 100!")
                return (False, deepcopy(grid))
        expanded_answer = []
        answer = deepcopy(grid)
        for row in answer:
            expanded_answer.extend(row)
        if not (expanded_answer in self.SOLUTIONS):
            self.SOLUTIONS.append(deepcopy(expanded_answer))
            self.COUNT += 1
            if self.COUNT > 100:
                raise TooManySolutionsException("Too many solutions! I counted at least 100!")
        return (True, answer)
    

    def GetCount(self) -> int:
        if self.COUNT != 0:
            return self.COUNT
        # else:
        self.CountSolve(self.grid)
        return self.COUNT


    def CheckValidGrid(self, inputgrid) -> bool:  # takes a solved or an unsolved grid and checks each row and column and box only once (9 total tiles) (using some tile coordinates written in the constants) for repeating numbers. returns True if no repeats and False if the grid was solved incorrectly.
        for i, j in self.CHECK_CELLS:
            row = inputgrid[i]
            item = row[j]
            row_neigh = [n for n in deepcopy(row) if n != 0]
            col_neigh = [_r[j] for _r in grid if _r[j] != 0]
            box_i = i // 3
            box_j = j // 3
            box_neigh = []
            for i_, row_ in enumerate(grid[box_i*3:(box_i+1)*3]):
                for j_, item_ in enumerate(row_[box_j*3:(box_j+1)*3]):
                    if item_ == 0:
                        continue
                    box_neigh.append(item_)
            if row_neigh != []:
                c_row = Counter(row_neigh)
                if c_row[max(c_row, key=lambda k: c_row[k])] > 1:
                    return False
            if col_neigh != []:
                c_col = Counter(col_neigh)
                if c_col[max(c_col, key=lambda k: c_col[k])] > 1:
                    return False
            if box_neigh != []:
                c_box = Counter(box_neigh)
                if c_box[max(c_box, key=lambda k: c_box[k])] > 1:
                    return False
        return True


def read_gridjpg_to_grid(kerasmodel, filename, grayscale_numpy_tiles_list_to_predicted_integer_list) -> list:
    global EMPTYGRID
    current_directory_files = [str(f) for f in os.listdir(os.getcwd())]
    if not (str(filename) in current_directory_files):
        print(colored(f"[>] The image '{filename}' isn't present in the current directory. Make sure to add it!", "magenta"))
        print(colored("[>] Returning an empty grid just for fun, while you go get your image.", "yellow"))
        print(colored("[>] No need to close the program; Just press the Enter key again and I'll process your image for you once you place it here.", "yellow"))
        raise Exception(f"Image file not found? Why? filename: {filename}, dir: {os.getcwd()}, ls: {os.listdir(os.getcwd())}")
        return (deepcopy(EMPTYGRID))
    tile_images = sudokuimagetool.process_image_file_to_list_of_polished_np_tiles(filename=filename)
    tiles = grayscale_numpy_tiles_list_to_predicted_integer_list(tiles=tile_images, model=kerasmodel)
    # print(tiles)
    grid = [tiles[i:i + 9] for i in range(0, 81, 9)]
    return (deepcopy(grid))


def write_grid_to_gridjpg(tiles_list: list, ogfilename: str, solvedfilename: str, gridname: str):
    print("saving to files...")
    largest_square, solved_grid, org_rgb_image, mostly_black = sudokuimagetool.write_solved_grid_to_image(newfilename=gridname, filename=ogfilename, tile_list=tiles_list)
    print("saved grid to it's own image.")
    gc.collect()
    sudokuimagetool.write_solved_grid_to_original_image(solvedfilename, largest_square, solved_grid, org_rgb_image, mostly_black)
    print("saved grid on the original image")


def main(model, filename, predict_grayscale_func) -> tuple:  
    # main thing with all of the main UX and styling going on. gets the time to solve, solves the grid, returns the amount of solutions and the first one.
    maingrid = read_gridjpg_to_grid(filename=filename, kerasmodel=model, grayscale_numpy_tiles_list_to_predicted_integer_list=predict_grayscale_func)
    
    print("\n")
    print(colored("Unsolved Grid:\n", "blue"))
    gridprint(maingrid)
    print("\n")
    
    st = time.time()
    
    solution = Solver(deepcopy(maingrid))
    couldbesolved, maingrid = solution.GuessworkSolve()
    solutions = solution.GetCount()

    et = time.time()
    dt = round(et - st, 4)
    
    print(colored(f"Time it took to count solutions and do the simplest solve: {dt} seconds", "magenta"))
    print(colored(f"The final grid is {'CORRECT' if couldbesolved else 'INCORRECT'}\n\n\n", "green" if couldbesolved else "red"))
    print(colored(f"The amount of solutions is {'only one!' if (solutions == 1) else f'{solutions}!'}\n\n\n", "lightblue" if (solutions == 1) else "blue"))

    if not couldbesolved:
        # expand on this
        # tell the user better details, as of right now this is WAYYY too broad
        # use different return codes
        return (-1, maingrid)

    print("\n")
    print(colored(f"{'The Solution' if (solutions == 1) else 'A Solution:'}:\n", "green"))
    gridprint(maingrid)
    print("\n")

    return (solutions, maingrid)


def servermain(filename, AImodel, predict_grayscale_func):
    global EMPTYGRID
    print('entering servermain')
    
    filename = str(filename)
    name, ext = map(str, getfilenameinfo(filename))
    gridname = str(f"{name}_solved_grid.{ext}")
    solvedname = str(f"{name}_solved.{ext}")
    
    print(f'name {name} ext {ext} gridname {gridname} solvedname {solvedname}')
    
    error_message, error_name, error_line = None, None, None

    try:
        countofsolutions, returnedgrid = main(model=AImodel, filename=filename, predict_grayscale_func=predict_grayscale_func)
        print("got a result")
    
    except TooManySolutionsException as err_message:
        print("got too many solutions")
        # return (True, gridname,  solvedname, deepcopy(GRID), str(err_message), 'Too many solutions', sys.exc_info()[-1].tb_lineno)
        error_message = str(err_message)
        error_name = "Too many solutions"
        error_line = sys.exc_info()[-1].tb_lineno

    except Exception as err_message:
        print("got an error")
        return (False, gridname, solvedname, deepcopy(EMPTYGRID), str(err_message), type(err_message).__name__, sys.exc_info()[-1].tb_lineno)
    
    if res == -1:
        print("got no result but no error")
        err_message_html: str = ("There's an error in one of the following:\n\n"
                            ""
                            "- <b>The image quality</b>\n"
                            "    <blockquote> Try sending a clearer picture, more zoomed in and clearer digits, and an obvious square grid with visibly distinct edges in the image. </blockquote>\n\n"
                            "- <b>The puzzle configuration</b>\n"
                            "    <blockquote> If you still face this message after the previous step, check the validty of your puzzle. </blockquote>\n\n"
                            "- <b>The program</b>\n"
                            "    <blockquote> If your image and puzzle are both correct and visible, report this issue to the admin on Telegram: <a href='https://t.me/FYI_PSA/'>@FYI_PSA</a> </blockquote>\n"
                            "")
        return (False, gridname, solvedname, returnedgrid, str(err_message_html), 'CouldNotBeSolved', 309)
    
    elif res > 1:
        print("got a bunch of results but less than a hundred")
        error_message = "The puzzle didn't have a unique solutions"
        error_name = "Solutions not unique"
        error_line = 400
    
    gc.collect()
    solved_tiles = []
    for row in GRID:
        solved_tiles.extend(row)
    print(f'desolved grid to {solved_tiles}')
    
    try:
        write_grid_to_gridjpg(solved_tiles, filename, solvedname, gridname)   
    except Exception as err:
        print('write to file failed with an error')
        error_message = str(err)
        error_name = type(err).__name__
        error_line = sys.exc_info()[-1].tb_lineno

    print('going home...')
    return (True, gridname, solvedname, returnedgrid, error_message, error_name, error_line)

    # success, name of solved grid file, name of solved full image file, completed or not grid as the 9 in 9 list, error message, error name, error line 


if __name__ == '__main__':
    servermain('screenshot.png')
    exit(0)

