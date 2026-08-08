"""
Contrôleurs simulés du véhicule.

Chaque fonction représente une action réelle qui serait effectuée sur le véhicule
(bus CAN, GPIO, etc.). Pour l'instant, on simule juste avec un état interne + des prints.
"""

class VehicleState:
    def __init__(self):
        self.music = {
            "on": False,                # initial state of music (on/off)
            "volume": 50,               # initial volume level (0-100)
            "Station": "Radio 1"        # initial station
        }
        self.temperature = {
            "value": 20                 # initial temperature in °C
        }
        self.speed = {
            "value": 0                  # initial speed in km/h (speed regulator)
        }
        self.lights = {
            "headlights": False,
            "luminosity": 50            # initial luminosity level (0-100)
        }
        self.navigation = {
            "destination": None,        # initial navigation destination (None if not set)
        }   
        self.fuel_level = { 
            "value": 100                # initial fuel level in percentage (0-100)
        }

    def __repr__(self):
        return (
            f"Vehicle states : \n\nMusic: {'ON' if self.music['on'] else 'OFF'}, volume: {self.music['volume']}, station: {self.music['Station']}\n"
            f"Temperature: {self.temperature['value']}°C\n"
            f"Speed: {self.speed['value']} km/h \n"
            f"Lights: {'ON' if self.lights['headlights'] else 'OFF'}, luminosity: {self.lights['luminosity']}\n"
            f"Navigation: destination: {self.navigation['destination']}\n"
            f"Fuel level: {self.fuel_level['value']}%\n"
        )


# Unique instance of the vehicle state
vehicle = VehicleState()

# Functions that simulate vehicle actions, which will be called by the orchestrator.

## Music settings

### Set music state (on/off)
def set_music_state(state: bool) -> str:
    vehicle.music['on'] = state
    action = "on" if state else "off"
    message = f"🎶 Music {action}."
    return message

### Set music volume (0-100)
def set_music_volume(volume: int) -> str:
    if not (0 <= volume <= 100):
        message = f"⚠️ Volume not allowed : {volume} is out of bounds (0-100)."
        return message

    vehicle.music['volume'] = volume
    message = f"🔊 Music volume set to {volume}."
    return message

### Set music station (string)
def set_music_station(station: str) -> str:
    vehicle.music['Station'] = station
    message = f"📻 Music station set to {station}."
    return message

## Temperature settings

### Set temperature (16-30°C)
def set_temperature_value(value: int) -> str:
    if not (16 <= value <= 30):
        message = f"⚠️ Temperature not allowed : {value}°C is out of bounds (16-30°C)."
        return message

    vehicle.temperature['value'] = value
    message = f"🌡️  Temperature set to {value}°C."
    return message

## Speed settings

### Set speed (0-200 km/h)
def set_speed_value(value: int) -> str:
    if not (0 <= value <= 200):
        message = f"⚠️ Speed not allowed : {value} km/h is out of bounds (0-200 km/h)."
        return message

    vehicle.speed['value'] = value
    message = f"🚗 Speed target set to {value} km/h."
    return message

## Lights settings

### Set lights state (on/off)
def set_lights_state(state: bool) -> str:
    vehicle.lights['headlights'] = state
    action = "on" if state else "off"
    message = f"💡 Headlights turned {action}."
    return message

### Set lights luminosity (0-100)
def set_lights_luminosity(luminosity: int) -> str:
    if not (0 <= luminosity <= 100):
        message = f"⚠️ Luminosity not allowed : {luminosity} is out of bounds (0-100)."
        return message

    vehicle.lights['luminosity'] = luminosity
    message = f"💡 Luminosity set to {luminosity}."
    return message

## Navigation settings

#### Set navigation destination (string)
def set_navigation_destination(destination: str) -> str:
    vehicle.navigation['destination'] = destination
    message = f"🗺️  Navigation destination set to {destination}."
    return message

## Fuel level settings

### Set fuel level (0-100%)
def set_fuel_level(value: int) -> str:
    if not (0 <= value <= 100):
        message = f"⚠️ Fuel level not allowed : {value}% is out of bounds (0-100%)."
        return message

    vehicle.fuel_level['value'] = value
    message = f"⛽ Fuel level set to {value}%."
    return message

### Get fuel level (0-100%)
def get_fuel_level() -> str:
    return f"⛽ Fuel level: {vehicle.fuel_level['value']}%."

## Get the complete state of the vehicle

def get_state() -> str:
    return repr(vehicle)


if __name__ == "__main__":
    # Petit test manuel du module
    print(set_music_state(True))
    print(set_music_volume(75))
    print(set_music_station("Radio 2"))
    print(set_temperature_value(20))
    print(set_speed_value(30))
    print(set_lights_state(True))
    print(set_lights_luminosity(80))
    print(set_navigation_destination("123 Main St"))
    print(set_fuel_level(50))
    print(get_fuel_level())
    print(get_state())