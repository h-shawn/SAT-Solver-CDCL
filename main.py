import argparse
import time

from cdcl import CDCL
from utils import read_cnf


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--input", type=str, default="examples/test.cnf"
    )

    return parser.parse_args()


def main(args):
    # Create problem.
    with open(args.input, "r") as f:
        sentence, num_vars = read_cnf(f)

    start_time = time.time()
    # Create CDCL solver and solve it!
    cdcl = CDCL(sentence, num_vars)
    res = cdcl.solve()

    if res is None:
        print("✘ No solution found")
    else:
        print(f"✔ Successfully found a solution")
        with open("output.log", "w") as o:
            o.write(str(res))
    end_time = time.time()
    print("time: "+str(end_time-start_time)+"s")


if __name__ == "__main__":
    args = parse_args()
    main(args)
