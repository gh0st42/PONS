class EnergyModel:
    """base class for energy models"""
    def __init__(self, max_energy: float, idle: float, receive: float, forward: float, name: str):
        """
        @param max_energy: max energy of the model
        @param idle: amount of energy the model consumes in idle
        @param receive: amount of energy the model consumes upon message receival
        @param forward: amount of energy the model consumes upon forward of message
        """
        self.max_energy: float = max_energy
        self._idle: float = idle
        self._receive: float = receive
        self._forward: float = forward
        self._name: str = name
        self.energy: float = max_energy

    def __str__(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return str(self)

    def on_receive(self):
        """handling message receive"""
        self.energy -= self._receive

    def on_forward(self):
        """handling message forward"""
        self.energy -= self._forward

    def on_idle(self, interval: float = 1.0):
        """handling idle"""
        self.energy -= self._idle * interval


class DefaultEnergyModel(EnergyModel):
    """unlimited energy model - equivalent to no energy model"""
    def __init__(self):
        super().__init__(100, 0, 0, 0, "DefaultEnergyModel")


class ESP32Wifi(EnergyModel):
    """energy model simulating the esp32 using wifi"""
    def __init__(self, initial_energy: int = 100000):
        super().__init__(initial_energy, 90, 100, 190, "ESP32 Wifi")
