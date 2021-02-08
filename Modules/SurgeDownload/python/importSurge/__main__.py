"""The main routine of my_project."""
# http://go.chriswarrick.com/entry_points

import sys
import importSurge
from importSurge import retrieveSurge


def main(args=None):
    """The main routine."""
    if args is None:
        args = sys.argv[1:]

    print("This is the main routine.")
    print("It should do something interesting.")

    # Generate diagnostic file
    print("writing file...")
    file = open("diagnostics.txt","w")
    file.write(retrieveSurge.retrieveSurgeFile())
    file.close()

    # Do argument parsing here (eg. with argparse) and anything else
    # you want your project to do. Return values are exit codes.


if __name__ == "__main__":
    main()