import time
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusIOException

def live_read_addresses(ip_address, port=502, unit_id=1, start_address=0, num_addresses=100, update_interval=1):
    client = ModbusTcpClient(ip_address, port=port)
    
    try:
        client.connect()
        print(f"Connected to {ip_address}:{port}")
        
        while True:
            print("\033[2J\033[H")  
            print(f"Live Modbus Reading - Press Ctrl+C to stop")
            print(f"Reading from address {start_address} to {start_address + num_addresses - 1}")
            print("-" * 40)
            
            for address in range(start_address, start_address + num_addresses):
                try:
                    result = client.read_holding_registers(address=address, count=1, unit=unit_id)
                    
                    if not result.isError():
                        print(f"Address {address}: {result.registers[0]}")
                    else:
                        print(f"Error reading address {address}")
                
                except ModbusIOException as e:
                    print(f"IO Exception for address {address}: {str(e)}")
                
                except Exception as e:
                    print(f"Unexpected error for address {address}: {str(e)}")
            
            print("-" * 40)
            print(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(update_interval)
    
    except KeyboardInterrupt:
        print("\nStopping live reading...")
    
    finally:
        client.close()
        print("Connection closed")

if __name__ == "__main__":
    modbus_ip = "127.0.0.1"  
    modbus_port = 502  
    unit_id = 1  
    start_address = 0
    num_addresses = 10  
    update_interval = 2  

    live_read_addresses(modbus_ip, modbus_port, unit_id, start_address, num_addresses, update_interval)