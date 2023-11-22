import numpy as np

def create_dynamic_grid(rows, columns):
    # Create a dynamic grid with the specified number of rows and columns
    grid = np.zeros((rows, columns), dtype=int)
    return grid

def print_grid(grid):
    # Print the grid
    for row in grid:
        print(" ".join(map(str, row)))

# Example usage
# rows = int(input("Enter the number of rows: "))
# columns = int(input("Enter the number of columns: "))

# grid = create_dynamic_grid(rows, columns)
print("\nInitial Grid:")
#print_grid(grid)
