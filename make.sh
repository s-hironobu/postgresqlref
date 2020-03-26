#!/bin/bash
for i in `ls text/*/*txt`; do
    ./ref.pl $i
done
