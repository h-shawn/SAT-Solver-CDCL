# SAT-Solver-CDCL

A simple SAT solver based on the CDCL (Conflict Driven Clause Learning) in Python

## Progress
+ [x] Basic SAT solver framework
+ [x] Implement restarting policy (Luby & Cadical)
+ [x] Implement MAB agent in restarting to choose branching heuristic
+ [x] Implement LRB branching heuristic
+ [x] Implement EVSIDS branching heuristic
+ [x] Implement CHB branching heuristic
+ [ ] Bonus requirements
  + [x] Bounded Variable Elimination (Currently BVE is called before main process only. Eliminates variables which positively/negatively appeared just once in the clause list.)
  + [x] Glue (LBD) reduction
  + [x] Subsumption Based Elimination
+ [ ] Debug, optimize and performance test
  + [x] Tested on bmc-x

## Instruction

Run any `.cnf` file 

```shell
python main.py -i ".cnf"
```

Run our testset

```shell
./runtest.sh
```

Moreover, you can modify parameters and options in `param.py`.