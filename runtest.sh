#!/bin/bash

trap 'exit 1' INT

SAT="./testset/sat"
UNSAT="./testset/unsat"

echo "running test..."

run(){
    start=`date +%s.%N`
    dir="$1/*"    
    for file in $dir; do
        echo "solving $file..."
        python3 main.py -i $file     
    done
    end=`date +%s.%N`
    runtime=$( echo "$end - $start" | bc -l )

    echo "total time: $runtime s"
}

echo "-----UNSAT-----"
run $UNSAT
echo 
echo "------SAT------"
run $SAT
