class PlayerAlreadyRegisteredError(Exception):
    """Exception raised when a player is already registered for a guild."""
    def __init__(self, guild_id):
        self.guild_id = guild_id
        self.message = f"A player is already registered for guild with ID {guild_id}."
        super().__init__(self.message)
