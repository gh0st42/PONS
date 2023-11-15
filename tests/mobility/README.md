# Mobility Tests

## NS2
### Running the tests
The tests can be run by simply running the python file they are in.
Most IDEs also support running tests out of their UI.

### What are we testing for?

Six tests -  testing for:
1. Metadata
2. Are all time steps present?
3. Are moves generated until the end time?
4. Is generation stopped early for a given end time?
5. Are moves generated from the start time?
6. Does generation start late for a given start time?+

### What kind of traces are provided?
[ns2_example_0_3600_18_3035.txt](ns2_example_0_3600_18_3035.txt) and [ns2_example_0_43200_18_43167.txt](ns2_example_0_43200_18_43167.txt) are default scenarios starting with a positive time. With the only difference being the duration.

[ns2_example_-500_3600_-482_3508.txt](ns2_example_-500_3600_-482_3508.txt) starts with a negative time.

The filename is constructed like this:
```ns2_example_<start_time>_<end_time>_<first_entry>_<last_entry>.txt```
- ```start_time```: the start time of the scenario
- ```end_time```: the end time of the scenario
- ```first_entry```: the floor of the first entry time
- ```last_entry```: the floor of the last entry time

```start_time``` and ```end_time``` are used in tests 3 and 5. They can be any value but the following constraints are recommended:
- ```start_time <= first_entry```
- ```end_time >= last_entry```

Start and end times not meeting these constraints are already tested with test 4 and 6.

More test files can be added at will. They just have to match the given format and have to be placed in the ```TESTFILES``` array in [ns2_tests.py](ns2_tests.py).