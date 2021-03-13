# AUTHOR: Daniel Raymond
# DATE  : 2020-04-30
# ABOUT : Combines all the circuits together into one fully functional beast

from LogitCalculator import LogitCalculator
from MaxLogitSelector import MaxLogitSelector
from src.data_packed import x_test, y_test

main = LogitCalculator()
MLS = MaxLogitSelector(
    EE_addr_width = main.FINAL_EEPROM.addr_width, 
    EE_io_width = main.FINAL_EEPROM.width
)
MLS.wire(
    main.FINAL_EEPROM, 
    main.done, 
    main.LAYER_SIZE.output, 
    main.clk
)

# * Run the program! (FINAL_EEPROM addr might crash it)
# main.predict(x_test[0])

main.FINAL_EEPROM.fill([118, 106, 110, 120, 120, 112, 100, 132, 106, 120])
main.done.value = 1

print('GUESS:', MLS.max_index.raw)
print('TRUE:', y_test[0])
