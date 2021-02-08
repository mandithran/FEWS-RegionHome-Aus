"""The main routine of importSurge package."""
# http://go.chriswarrick.com/entry_points

import sys
import importSurge
from importSurge import retrieveSurge


def main(args=None):
    """The main routine."""
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    print("This is the main routine.")
    print("It should do something interesting.")

    # Generate diagnostic file
    print("writing file...")
    file = open("diagnostics.txt","w")
    file.write(retrieveSurge.retrieveSurgeFile())
    # Print arguments from FEWS to diagnostics file
    if args:
        for a in args:
            file.write(str(a))
    file.close()


if __name__ == "__main__":
    main()