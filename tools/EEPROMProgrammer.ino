// TITLE:   EEPROM Programmer
// PURPOSE: To burn EEPROMs with models and input data
// AUTHOR:  Daniel Raymond
// DATE:    2020-08-17
// STATUS:  Not Functional

#define DATA  1 << PB0  // Digital pin 8
#define LATCH 1 << PB1  // Digital pin 9
#define CLK   1 << PB2  // Digital pin 10
#define EE_WE 1 << PB3  // Digital pin 11
#define EE_OE 1 << PB4  // Digital pin 12
#define SR_OE 1 << PB5  // Digital pin 13

void shiftOut(uint8_t serialData);
void writeData(uint8_t addr, uint8_t data);
void readData(uint8_t addr);

void setup() {
  Serial.begin(9600);
  DDRB = DATA | LATCH | CLK | EE_WE | EE_OE | SR_OE; // Set pins to output
  PORTB = LATCH | CLK | SR_OE; // Start in write mode
  // Flush out the SRs
  shiftOut(0x00);
  shiftOut(0x00);

  // readData(0xFF);
}

void loop() {}


void readData(uint8_t addr) {
  // Clear High impedance on the SRs output
  // PORTB &= ~(1 << SR_OE);
  // // Let the EEPROM output
  // PORTB |= 1 << EE_OE;
  // Shift out the address
  shiftOut(addr);
}

void writeData(uint8_t addr, uint8_t data) {
  // Let EEPROM take in data
  // PORTB &= ~(1 << EE_OE);
  // // Let the SRs output
  // PORTB |= 1 << SR_OE;

  // Shift out address and data
  shiftOut(addr);
  shiftOut(data);

  // Flash the write pin low on the EEPROM
  // PORTB &= ~(1 << EE_WE); 
  // delay(5);
  // PORTB |= 1 << EE_WE; 
}

void shiftOut(uint8_t serialData) {
    PORTB &= ~(LATCH); // Set latch low
    // Iterate through data (bits in serialData)
    for (int i = 0; i < sizeof(serialData)*8; i++) {
        PORTB &= ~(CLK); // Clear the clock
        uint8_t bit = serialData & (1 << i); // Isolate bit

        // Set/clear the data bit
        if (bit) PORTB |= DATA;
        else     PORTB &= ~(DATA);

        PORTB |= CLK; // Set the clock
    }
    PORTB |= LATCH;
    delay(10);
}
