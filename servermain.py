import os
import sys
from copy import deepcopy
import time
from collections import Counter
import sudokuimagetool

from typing import List, Tuple

import numpy as np

import gc

if os.name != "nt":
    # When on Linux => Os.name not "nt" => Switch to logging instead of printing, particularly for deploying to servers.
    # When on Windows => Os.name = "nt" => Only print
    import logging
    print = logging.info


def get_file_name_info(file_name: str) -> Tuple[str, str]:
    # print(file_name)
    filename = str(file_name)
    splitname = filename.split('.')
    ext = splitname[-1]
    actual_name = ''.join(splitname[0:-1])
    result = (actual_name, ext)
    # print(result)
    return result


def gridstring(grid):
    # widest_item_lengths_per_row = [max([len(str(item)) for item in row]) for row in grid]
    # pad_length = max(widest_item_lengths_per_row) + 1
    pad_length = max((max(len(str(i)) for i in row) for row in grid)) + 1
    gap_length = round(pad_length*1.1)
    gridstr = ''
    for row_i, row in enumerate(grid):
        for col_j, item_ in enumerate(row):
            item = str(item_)
            gridstr += item
            gridstr += str(' ' * (pad_length - len(item)))
            if col_j == 8:
                continue
            if (col_j % 3) == 2:
                gridstr += str(' ' * (gap_length))
        if (row_i % 3) == 2:
            gridstr += str('\n\n')
        gridstr += str('\n')
    return gridstr


def gridprint(grid):
    gridstr = gridstring(grid)
    print(gridstr)


def colored(text, color):  # pylint: disable=W0613
    # This is quick and dirty lol
    return text


def break_down_to_set(small_list_or_str):
    larger_set = set()
    if isinstance(small_list_or_str, str):
        input = str(small_list_or_str).strip().lower()
    else:
        input = small_list_or_str
    if input in ('', []):
        return larger_set
    for _ in input:
        if isinstance(_, int):
            larger_set.add(_)
        elif _ == '-':
            continue
        elif isinstance(_, bool):
            raise Exception("Somehow a boolean array is passed to be broken into a set")
        else:
            try:
                larger_set = larger_set | (set(map(int, _.split('-'))))
            except ValueError as v_err:
                raise Exception(f"Somehow something that's not a bool, int, or number str, is passed to be broken into a set:\nItem: ({_}), Type: ({type(_)})") from v_err
    return larger_set


global EMPTYGRID  # pylint: disable=W0604
EMPTYGRID = [[0 for _ in range(9)] for _ in range(9)]


def grid_to_list(grid: List[List[int]]) -> List[int]:
    result = []
    for row in grid:
        result.extend(row)
    return result


def back_to_grid(grid_list: List[int] | np.ndarray) -> List[List[int]]:
    grid_list_ = list(map(int, np.asarray(grid_list, dtype=np.uint8)))
    # ensure that no matter what it is it gets turned into a python list of python ints
    return [grid_list_[i:i+9] for i in range(0, 81, 9)]


def grid_list_to_np(grid_list) -> np.ndarray:
    return np.array([np.asarray(row) for row in grid_list])


class Solver():
    def __init__(self, grid: list):
        self.ALL = set(range(1, 10))  # pylint: disable=C0103
        self.CHECK_CELLS = [(0, 0), (1, 3), (2, 6), (3, 1), (4, 4), (5, 7), (6, 2), (7, 5), (8, 8)]  # pylint: disable=C0103
        # Definitely mathematically redundant and can be reduced.
        # I don't want to do that though, too lazy. Deal with it, it's not slow enough to care about.
        self.SOLUTIONS = set()  # pylint: disable=C0103
        self.COUNT = 0  # pylint: disable=C0103
        self.GRID = deepcopy(grid)  # pylint: disable=C0103
        self.first_grid = deepcopy(self.GRID)
        self.first_solution = deepcopy(self.GRID)

    def solve_by_grid(self, input_grid) -> Tuple[List[List[int]], List[List[int]]]:
        # takes a base grid and tries to solve for lonely items. returns a candidate-filled kinda-solved grid and the normal kinda-solved grid
        grid = deepcopy(input_grid)
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
                    for row_ in grid[box_i*3:(box_i+1)*3]:
                        for item_ in row_[box_j*3:(box_j+1)*3]:
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

    def solve_by_candid(self, input_candids, input_grid) -> List[List[int]]:
        # takes a candidate-containing grid and the normal grid and tries to solve based on being the only candidate for a number in a set. returns a kinda-solved normal grid
        candid = deepcopy(input_candids)
        grid = deepcopy(input_grid)
        for i, row in enumerate(candid):
            for j, item in enumerate(row):
                if not isinstance(item, int):
                    # item_superposition = set(map(int, item.split('-')))
                    # # Never used, but I'm too afraid to remove this.
                    # I commented it, here's hoping for the best lol
                    neighbour_row = [k for (_, k) in enumerate(row) if (_ != j)]
                    n_r = break_down_to_set(neighbour_row)
                    neighbour_col = [r_[j] for (k, r_) in enumerate(candid) if (k != i)]
                    n_c = break_down_to_set(neighbour_col)
                    box = []
                    box_i = i // 3
                    box_j = j // 3
                    for i_, row_ in enumerate(candid[box_i*3:(box_i+1)*3]):
                        for j_, item_ in enumerate(row_[box_j*3:(box_j+1)*3]):
                            if i_ == (i % 3) and j_ == (j % 3):
                                continue
                            box.append(item_)
                    n_b = break_down_to_set(box)
                    # THIS OPERATION IS NOT GLOBAL
                    # IT APPLIES SEPARATELY TO EACH LOCK
                    #   What did I mean by this when I added it when first writing this?? I genuinely don't know...
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

    def simple_solve(self, input_grid) -> Tuple[List[List[int]], List[List[int]]]:
        # takes a normal unsolved grid, and tries to solve it using the two functions above. returns a potentially candidate-containing grid and a potentially solved grid.
        grid = deepcopy(input_grid)
        candid = deepcopy(grid)
        copy_grid = deepcopy(EMPTYGRID)
        copy_candid = deepcopy(EMPTYGRID)
        copy_total = deepcopy(EMPTYGRID)
        first_total = True
        first_grid = True
        first_candid = True
        while copy_total != grid or first_total:
            first_total = False
            copy_total = deepcopy(grid)
            while copy_grid != grid or first_grid:
                first_grid = False
                copy_grid = deepcopy(grid)
                candid, grid = self.solve_by_grid(grid)
            # runs until solve_by_grid doesn't change grid
            while copy_candid != grid or first_candid:
                first_candid = False
                copy_candid = deepcopy(grid)
                grid = self.solve_by_candid(candid, grid)
            # runs until solve_by_candid doesn't change grid
            candid, grid = self.solve_by_grid(grid)
            # this last step is to generate the candid grid
        return (candid, grid)

    # solves the grid by trying the simple solve methods on it,
    #   "simple_solve" method:
    #     1.single possibility tiles become just that possibility,
    #     2.if a number can only be in once space of a row/column/box, then that tile becomes the number it can only be there.
    # then applying a brute force technique to any unsolved tiles and then trying itself again.
    # takes an unsolved grid as input and returns a boolean for it was solvable alongside a hopefully solved grid.
    def OLD_GuessworkSolve(self, grid_base, debug=False) -> Tuple[bool, List[List[int]]]:  # pylint: disable=C0103
        candid, grid = self.simple_solve(grid_base)
        if not self.check_valid_grid(grid):
            return (False, grid)
        if debug:
            print(colored("[#] Debug turn:\n", "light_yellow"))
            gridprint(candid)
            print("")
        for i, row in enumerate(grid):
            for j, item in enumerate(row):
                if item != 0:
                    continue
                candidate_string = candid[i][j]
                # If a set is of length less than one, then simple_solve doesn't assign it a candidate string in the candidates, leaving it as 0.
                if not isinstance(candidate_string, str):
                    if debug:
                        print(colored("[#] *BEEP*! Reached a wrong answer, sorry!", "magenta"))
                    return (False, deepcopy(grid))
                candidates = break_down_to_set(candidate_string)

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
                    test_grid = []
                    test_grid = deepcopy(grid)
                    test_grid[i][j] = p
                    could_be_solved, answer = self.OLD_GuessworkSolve(test_grid, debug=debug)
                    if could_be_solved and self.check_valid_grid(answer):
                        return (True, answer)
                # it's impossible for it not to be one of the values that are possible for a number, so if reaching this point, automatically assume failure.
                if debug:
                    print(colored("[#] Assuming failure.", "magenta"))
                return (False, deepcopy(grid))
        # by this point:
        # the grid must already be solved, not be wrong, not have any emptiness
        # so it'll always return True on check_valid_grid
        return (True, deepcopy(grid))

    def brute_all_solves(self, grid_base) -> List[List[int]]:
        candid, grid = self.simple_solve(grid_base)
        if not self.check_valid_grid(grid):
            return (grid)

        for i, row in enumerate(grid):
            for j, item in enumerate(row):
                if item != 0:
                    continue

                candidate_string = candid[i][j]
                if not isinstance(candidate_string, str):  # Means it's an int and is 0 for empty
                    return (deepcopy(grid))
                candidates = break_down_to_set(candidate_string)
                for r_ in candid:
                    for j_ in r_:
                        if j_ == 0:
                            return (deepcopy(grid))

                candidates = list(candidates)
                candidates.sort()

                for p in candidates:
                    test_grid = deepcopy(grid)
                    test_grid[i][j] = p
                    answer = self.brute_all_solves(test_grid)
                    if self.COUNT > 100:
                        return (answer)
                    if self.check_valid_grid(answer) and self.check_is_solved(answer):
                        answer_tuple = tuple(grid_to_list(answer))
                        if answer_tuple not in self.SOLUTIONS:
                            self.SOLUTIONS.add(deepcopy(answer_tuple))
                            self.COUNT = self.COUNT + 1
                        if self.COUNT == 1:
                            self.first_solution = answer
                        del answer_tuple
                    del test_grid

                return (deepcopy(grid))
        # reaching this point, grid is full.
        answer = grid
        if self.COUNT > 100:
            return (answer)
        if self.check_valid_grid(answer) and self.check_is_solved(answer):
            answer_tuple = tuple(grid_to_list(answer))
            if answer_tuple not in self.SOLUTIONS:
                self.SOLUTIONS.add(deepcopy(answer_tuple))
                self.COUNT = self.COUNT + 1
            if self.COUNT == 1:
                self.first_solution = answer
        return (grid)

    def count_and_solve(self) -> Tuple[bool, int, List[List[int]]]:
        if self.check_is_solved(self.GRID):
            self.COUNT = max(1, self.COUNT)  # in case it's being fed an already fully solved grid.
            return (True, self.COUNT, self.first_solution)
        self.brute_all_solves(deepcopy(self.first_grid))
        self.GRID = deepcopy(self.first_solution)
        if (not self.check_is_solved(self.GRID)) and (self.COUNT > 0):
            raise BadInspectionException("I somehow messed up.")
        status = False
        if self.COUNT > 0:
            status = True
        return (status, self.COUNT, self.first_solution)

    def get_solution_from_index(self, index: int) -> List[List[int]]:
        if self.COUNT <= index:
            error_message = "Your requested index of solutions didn't exist. Generate first, and be reasonable."
            print(error_message)
            raise IndexError(error_message)
        return back_to_grid(list(list(self.SOLUTIONS)[index]))
    # WARNING: self.SOLUTIONS IS A SET, THE LIST CONVERSION WILL BE SEMI-RANDOM

    def check_valid_grid(self, input_grid=None) -> bool:
        if input_grid is None:
            input_grid = deepcopy(self.GRID)
        # takes a solved or an unsolved grid
        # and checks each row and column and box only once for repeating numbers
        # (9 tiles total) (using some tile coordinates in the class attributes)
        # returns True if no repeats and False if the grid was solved incorrectly.
        for i, j in self.CHECK_CELLS:
            row = input_grid[i]
            # item = row[j]
            row_neigh = [n for n in deepcopy(row) if n != 0]
            col_neigh = [_r[j] for _r in input_grid if _r[j] != 0]
            box_i = i // 3
            box_j = j // 3
            box_neigh = []
            for row_ in input_grid[box_i*3:(box_i+1)*3]:
                for item_ in row_[box_j*3:(box_j+1)*3]:
                    if item_ == 0:
                        continue
                    box_neigh.append(item_)
            if row_neigh != []:
                current_row = Counter(row_neigh)
                if any((current_row_count > 1) for current_row_count in current_row.values()):
                    return False
            if col_neigh != []:
                current_col = Counter(col_neigh)
                if any((current_col_count > 1) for current_col_count in current_col.values()):
                    return False
            if box_neigh != []:
                current_box = Counter(box_neigh)
                if any((current_box_count > 1) for current_box_count in current_box.values()):
                    return False
        return True

    def check_is_solved(self, grid_input: List[List[int]]) -> bool:
        for row in grid_input:
            for item in row:
                if item == 0:
                    return False
        return self.check_valid_grid(grid_input)


class BadInspectionException(Exception):
    pass


def generate_puzzle(diff: int = 0) -> List[List[int]]:
    """Makes a Sudoku puzzle grid based on the difficulty provided

    Args:
        diff (int, optional): For each level, it adds one additional tile of information. Defaults to 0 for hard mode.

    Returns:
        list: The unsolved puzzle, as a 9 by 9 list.
    """
    # get a solver object in here
    # fill in the diagonal randomly (and more later)
    # generate_count_of_solutions, or don't, I think it's mathematically calculable if it's just the diagonal. save as magic number.
    # generate all solutions with the solver object
    # randomly choose one.
    # then continue with this:

    flat_grid = list(map(int, np.zeros(81)))

    base_flat = None
    works = False
    while not works:
        base_flat = deepcopy(flat_grid)
        for i in range(9):
            random = 1.0 - np.random.rand()
            random = random * 0.9
            random = int(np.ceil(random * 100) // 10)
            base_flat[10*i] = random
        works = Solver(back_to_grid(base_flat)).check_valid_grid()
    base_scramble = (flat_grid if base_flat is None else base_flat)

    test_base_scramble = None
    works = False
    while not works:
        test_base_scramble = deepcopy(base_scramble)
        for i in range(9):
            random = 1.0 - np.random.rand()
            random = random * 0.9
            random = int(np.ceil(random * 100) // 10)
            test_base_scramble[8*(i+1)] = random
            # 8*(i+1) and 10*(i) values are magic numbers that give the indices of the main diagonals with i
        works = Solver(back_to_grid(test_base_scramble)).check_valid_grid()
    scrambled_diagonals = (base_scramble if test_base_scramble is None else test_base_scramble)
    grid_scrambled = back_to_grid(scrambled_diagonals)

    solve_it = Solver(grid_scrambled)
    try:
        possible, count, _ = solve_it.count_and_solve()
        if not possible:
            raise BadInspectionException("How in the hell did this thing pass inspection?")
    except BadInspectionException as e:
        print(f"The code failed due to bad inspection: {e}")
        return EMPTYGRID
    except Exception as e:
        print("Generic exception while generating puzzle? That's strange.")
        raise e

    assert (count > 0)  # otherwise the above exception would be raised
    # asserting this in case I miscalculated something in my algorithm

    random = np.random.rand()
    random = int(np.floor(random*100*count) / 100)

    if not (-1 < random < count):
        print('Random is choosing incorrectly?')
        random = random % count

    print(f"Out of {count} possible grids, #{random} was chosen.")

    full_grid = solve_it.get_solution_from_index(random)

    indices = np.arange(0, 81, 1)
    np.random.shuffle(indices)
    np.random.shuffle(indices)
    np.random.shuffle(indices)
    # Three time's the charm!

    solved_grid = []
    for r in full_grid:
        solved_grid.extend(r)

    cond = True
    middle = 81 // 2
    count = 1
    while cond:
        given_indices = indices[:middle+1]
        new_grid = back_to_grid([item if (index in given_indices) else 0 for index, item in enumerate(solved_grid)])
        tester = Solver(new_grid)
        possible, count, _ = tester.count_and_solve()
        middle = middle // 2
        if count != 1 or middle == 0:
            cond = False
        del tester
        del new_grid
    while count > 1:
        given_indices = indices[:middle+1]
        new_grid = back_to_grid([item if index in given_indices else 0 for index, item in enumerate(solved_grid)])
        tester = Solver(new_grid)
        possible, count, _ = tester.count_and_solve()
        if count > 1:
            middle += 1

    middle = middle + diff
    given_indices = indices[:middle+1]
    new_grid = back_to_grid([item if index in given_indices else 0 for index, item in enumerate(solved_grid)])

    return new_grid


def read_grid_picture_to_grid(keras_model, filename: str, predict_grayscale_function) -> List[List[int]]:
    current_directory_files = [str(f) for f in os.listdir(os.getcwd())]
    if not (str(filename) in current_directory_files):
        print(colored(f"[>] The image '{filename}' isn't present in the current directory. Make sure to add it!", "magenta"))
        print(colored("[>] Returning an empty grid just for fun, while you go get your image.", "yellow"))
        print(colored("[>] No need to close the program; Just press the Enter key again and I'll process your image for you once you place it here.", "yellow"))
        raise Exception(f"Image file not found? Why? filename: {filename}, dir: {os.getcwd()}, ls: {os.listdir(os.getcwd())}")
    tile_images = sudokuimagetool.process_image_file_to_list_of_polished_np_tiles(filename=filename)
    tiles = predict_grayscale_function(tiles=tile_images, model=keras_model)
    grid = [tiles[i:i + 9] for i in range(0, 81, 9)]
    return (deepcopy(grid))


def write_grid_to_grid_picture(tiles_list: list, og_file_name: str, solved_file_name: str, grid_name: str):
    print("saving to files...")
    largest_square, solved_grid, org_rgb_image, mostly_black = sudokuimagetool.write_solved_grid_to_image(new_file_name=grid_name, filename=og_file_name, tile_list=tiles_list)
    print("saved grid to it's own image.")
    gc.collect()
    sudokuimagetool.write_solved_grid_to_original_image(solved_file_name, largest_square, solved_grid, org_rgb_image, mostly_black)
    print("saved grid on the original image")


def main(model, filename, predict_grayscale_func) -> Tuple[int, List[List[int]]]:
    # main thing with all of the main UX and styling going on. gets the time to solve, solves the grid, returns the amount of solutions and the first one.
    main_grid = read_grid_picture_to_grid(filename=filename, keras_model=model, predict_grayscale_function=predict_grayscale_func)

    print("\n")
    print(colored("Unsolved Grid:\n", "blue"))
    gridprint(main_grid)
    print("\n")

    st = time.time()

    solution = Solver(deepcopy(main_grid))
    could_be_solved, number_of_solutions, first_solution = solution.count_and_solve()

    et = time.time()
    dt = round(et - st, 4)

    print(colored(f"Time it took to count solutions and do the simplest solve: {dt} seconds", "magenta"))
    print(colored(f"The final grid is {'CORRECT' if could_be_solved else 'INCORRECT'}\n\n\n", "green" if could_be_solved else "red"))
    print(colored(f"The amount of solutions is {'only one!' if (number_of_solutions == 1) else f'{number_of_solutions}!'}\n\n\n", "lightblue" if (number_of_solutions == 1) else "blue"))

    if not could_be_solved:
        # expand on this
        # tell the user better details, as of right now this is WAY TOO BROAD
        # use different return codes
        return (-1, first_solution)

    print("\n")
    print(colored(f"{'The Solution' if (number_of_solutions == 1) else 'A Solution:'}:\n", "green"))
    gridprint(first_solution)
    print("\n")

    return (number_of_solutions, first_solution)


def servermain(filename, ai_model, predict_grayscale_func) -> Tuple[bool, str, str, List[List[int]], str | None, str | None, int | None]:
    print('entering servermain')

    filename = str(filename)
    name, ext = map(str, get_file_name_info(filename))
    grid_name = str(f"{name}_solved_grid.{ext}")
    solved_name = str(f"{name}_solved.{ext}")

    print(f"name: {name} |  ext: {ext} |  grid_name: {grid_name} |  solved_name: {solved_name}")

    solved_status = True
    error_message, error_name, error_line = None, None, None

    try:
        count_of_solutions, returned_grid = main(model=ai_model, filename=filename, predict_grayscale_func=predict_grayscale_func)
        print("got a result")
    except Exception as err_message:
        print("got an error")
        print(err_message)
        last_event = sys.exc_info()[-1]
        error_line = (-1 if last_event is None else last_event.tb_lineno)
        print(f'error line: {error_line}')
        sys.exit(1)
        # return (False, grid_name, solved_name, deepcopy(EMPTYGRID), str(err_message), type(err_message).__name__, sys.exc_info()[-1].tb_lineno)
        # RETURN THIS AGAIN IF YOU REMOVE THE EXIT(1)

    if count_of_solutions == -1:  # it's when (could_be_solved == False)
        print("The code progressed all the way here, but (could_be_solved) was False")
        err_message_html: str = (
            "There's an issue with one of the following:\n\n"
            ""
            "- <b>The image quality</b>\n"
            "    <blockquote> Try sending a clearer picture, more zoomed in and clearer digits, and an obvious square grid with visibly distinct edges in the image. </blockquote>\n\n"
            "- <b>The puzzle configuration</b>\n"
            "    <blockquote> If you still face this message after the previous step, check that your puzzle is indeed valid and has a solution. </blockquote>\n\n"
            "- <b>The image recognition</b>\n"
            # "    <blockquote> If your image and puzzle are both correct and visible, report this issue to the admin on Telegram: <a href='https://t.me/FYI_PSA/'>@FYI_PSA</a> </blockquote>\n"
            "    <blockquote> If your image and puzzle are both correct and visible, report this issue to the admin on Telegram: @FYI_PSA </blockquote>\n"
            ""
            )
        solved_status = False
        error_message = str(err_message_html)
        error_name = 'CouldNotBeSolved'
        error_line = 589
    # put these two in elif, because the lack of solutions is more important
    # (even though count_of_solutions should still be 0 and thus wouldn't cause problems)
    elif 1 < count_of_solutions <= 100:
        print("got a bunch of results but it's not more than a hundred")
        error_message = "The puzzle didn't have a unique solutions"
        error_name = "Solutions not unique"
        error_line = 596
    elif count_of_solutions > 100:
        print("got too many solutions")
        # count_of_solutions = 101  # I'm 99% sure with the new code, it already is 101.
        error_message = "This puzzle has at least 100 solutions!"
        error_name = "Too many solutions"
        error_line = 602

    gc.collect()
    solved_tiles = []
    for row in returned_grid:
        solved_tiles.extend(row)
    print(f'dissolved grid to {solved_tiles}')

    try:
        write_grid_to_grid_picture(solved_tiles, filename, solved_name, grid_name)
    except Exception as err:
        print('write to file failed with an error')
        error_message = str(err)
        error_name = type(err).__name__
        last_event = sys.exc_info()[-1]
        error_line = (-1 if last_event is None else last_event.tb_lineno)

    print('going home...')
    return (solved_status, grid_name, solved_name, returned_grid, error_message, error_name, error_line)
    # return value:
    # successful as a boolean, name of solved grid file as a string, name of solved full image file as a string, completed or not grid as 9 lists of 9 numbers in a list, error message as a string, error name as a string, error line as an int


if __name__ == '__main__':

    # TEST = 'PUZZLE'  # to test if the puzzle generation works
    # TEST = 'READ'  # to test if the image reading works
    TEST = 'SERVER'  # to test the main() and servermain() functions
    # TEST = 'EMPTY'  # to test if the ordering of solutions is correct

    match TEST:
        case 'PUZZLE':
            _puzzle = generate_puzzle()
            _main_grid = deepcopy(_puzzle)
            print("\n")
            print("Generated Puzzle:")
            gridprint(_puzzle)
            print("\n")
        case 'READ':
            from tilereader import load_model
            from tilereader import grayscale_numpy_tiles_list_to_predicted_integer_list as predict_function
            loaded_model = load_model()
            _main_grid = read_grid_picture_to_grid(loaded_model, 'screenshot.png', predict_function)
        case 'SERVER':
            from tilereader import load_model
            from tilereader import grayscale_numpy_tiles_list_to_predicted_integer_list as predict_function
            loaded_model = load_model()
            servermain('screenshot.png', loaded_model, predict_function)
            sys.exit(0)
        case _:
            _main_grid = EMPTYGRID

    # currently has an issue where the cv2.putText fonts is causing it to see it's own response's 3s as 5s.
    # TODO: fix this.

    print("\n")
    print("Target Puzzle:")
    gridprint(_main_grid)
    print("\n")

    _st = time.time()

    # solution = Solver(deepcopy(main_grid))
    _solution = Solver(deepcopy(_main_grid))
    _could_be_solved, _number_of_solutions, _first_solution = _solution.count_and_solve()

    _et = time.time()
    _dt = round(_et - _st, 4)

    print(f"Time it took to count solutions and do the simplest solve: {_dt} seconds")
    print(f"The final grid is {'CORRECT' if _could_be_solved else 'INCORRECT'}\n\n")
    print(f"The amount of solutions is {'only one!' if (_number_of_solutions == 1) else f'{_number_of_solutions}!'}\n\n")

    print("\n")
    print("Solved Puzzle:")
    gridprint(_first_solution)
    print("\n")

    sys.exit(0)
