"""
Currency conversion cog.

Provides currency conversion commands between CNY, ZAR, and USD with daily rate caching.
"""

import aiohttp
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Dict, Optional
import discord
from discord import app_commands
from discord.ext import commands

from cogs.base_cog import BaseCog
from utils.helpers import create_embed, create_error_embed


class CurrencyConverter(BaseCog):
    """Currency conversion cog with exchange rate caching."""
    
    SUPPORTED_CURRENCIES = ["CNY", "ZAR", "USD"]
    
    # Fallback rates (updated 2025-11-25)
    FALLBACK_RATES = {
        "USD": 1.0,
        "CNY": 7.24,
        "ZAR": 18.12
    }
    
    def __init__(self, bot: commands.Bot):
        """Initialize the currency converter."""
        super().__init__(bot)
        self.rates: Dict[str, float] = {}
        self.last_update: Optional[datetime] = None
        self.cache_duration = timedelta(days=1)
    
    async def fetch_exchange_rates(self) -> bool:
        """
        Fetch current exchange rates from API.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Using exchangerate-api.com free tier (no API key needed for basic use)
            url = "https://api.exchangerate-api.com/v4/latest/USD"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.rates = {
                            "USD": 1.0,
                            "CNY": data["rates"].get("CNY", self.FALLBACK_RATES["CNY"]),
                            "ZAR": data["rates"].get("ZAR", self.FALLBACK_RATES["ZAR"])
                        }
                        self.last_update = datetime.utcnow()
                        self.logger.info(f"Exchange rates updated: {self.rates}")
                        return True
                    else:
                        self.logger.warning(f"Failed to fetch rates: HTTP {response.status}")
                        return False
        except Exception as e:
            self.logger.error(f"Error fetching exchange rates: {e}", exc_info=e)
            return False
    
    async def get_exchange_rates(self) -> Dict[str, float]:
        """
        Get current exchange rates, fetching if cache is stale.
        
        Returns:
            Dict[str, float]: Exchange rates with USD as base
        """
        # Check if we need to refresh rates
        if (not self.rates or 
            not self.last_update or 
            datetime.utcnow() - self.last_update > self.cache_duration):
            
            self.logger.info("Exchange rates cache is stale, fetching new rates...")
            success = await self.fetch_exchange_rates()
            
            if not success:
                self.logger.warning("Using fallback exchange rates")
                self.rates = self.FALLBACK_RATES.copy()
                self.last_update = datetime.utcnow()
        
        return self.rates
    
    def convert_currency(
        self, 
        amount: Decimal, 
        from_currency: str, 
        to_currency: str, 
        rates: Dict[str, float]
    ) -> Decimal:
        """
        Convert an amount from one currency to another.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            rates: Exchange rates dictionary
        
        Returns:
            Decimal: Converted amount
        """
        # Convert to USD first (base currency)
        amount_in_usd = amount / Decimal(str(rates[from_currency]))
        
        # Convert from USD to target currency
        result = amount_in_usd * Decimal(str(rates[to_currency]))
        
        return result
    
    @app_commands.command(
        name="convert",
        description="Convert currency between CNY, ZAR, and USD"
    )
    @app_commands.describe(
        amount="Amount to convert",
        from_currency="Currency to convert from (CNY, ZAR, USD)",
        to_currency="Currency to convert to (CNY, ZAR, USD)"
    )
    async def convert(
        self,
        interaction: discord.Interaction,
        amount: str,
        from_currency: str,
        to_currency: str
    ):
        """
        Convert currency command.
        
        Args:
            interaction: Discord interaction
            amount: Amount to convert
            from_currency: Source currency
            to_currency: Target currency
        """
        # Defer response since we might need to fetch rates
        await interaction.response.defer()
        
        # Normalize currency codes
        from_currency = from_currency.upper().strip()
        to_currency = to_currency.upper().strip()
        
        # Validate currencies
        if from_currency not in self.SUPPORTED_CURRENCIES:
            await interaction.followup.send(
                embed=create_error_embed(
                    f"Invalid source currency: `{from_currency}`. "
                    f"Supported: {', '.join(self.SUPPORTED_CURRENCIES)}"
                )
            )
            return
        
        if to_currency not in self.SUPPORTED_CURRENCIES:
            await interaction.followup.send(
                embed=create_error_embed(
                    f"Invalid target currency: `{to_currency}`. "
                    f"Supported: {', '.join(self.SUPPORTED_CURRENCIES)}"
                )
            )
            return
        
        # Same currency check
        if from_currency == to_currency:
            await interaction.followup.send(
                embed=create_error_embed(
                    "Source and target currencies cannot be the same!"
                )
            )
            return
        
        # Parse amount
        try:
            amount_decimal = Decimal(amount.replace(",", ""))
            if amount_decimal <= 0:
                await interaction.followup.send(
                    embed=create_error_embed("Amount must be greater than 0!")
                )
                return
        except (InvalidOperation, ValueError):
            await interaction.followup.send(
                embed=create_error_embed(f"Invalid amount: `{amount}`")
            )
            return
        
        # Get exchange rates
        rates = await self.get_exchange_rates()
        
        # Perform conversion
        converted_amount = self.convert_currency(
            amount_decimal,
            from_currency,
            to_currency,
            rates
        )
        
        # Currency symbols
        symbols = {
            "USD": "$",
            "CNY": "¥",
            "ZAR": "R"
        }
        
        # Create embed response
        embed = create_embed(
            title="💱 Currency Conversion",
            color=discord.Color.blue(),
            fields=[
                ("From", f"{symbols[from_currency]}{amount_decimal:,.2f} {from_currency}", True),
                ("To", f"{symbols[to_currency]}{converted_amount:,.2f} {to_currency}", True),
                ("Rate", f"1 {from_currency} = {rates[to_currency]/rates[from_currency]:.4f} {to_currency}", False)
            ],
            footer=f"Rates last updated: {self.last_update.strftime('%Y-%m-%d %H:%M UTC') if self.last_update else 'Unknown'}"
        )
        
        await interaction.followup.send(embed=embed)
        self.logger.info(
            f"Currency conversion: {amount_decimal} {from_currency} -> "
            f"{converted_amount:.2f} {to_currency} for user {interaction.user}"
        )
    
    @convert.autocomplete("from_currency")
    async def from_currency_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for from_currency parameter."""
        return [
            app_commands.Choice(name=currency, value=currency)
            for currency in self.SUPPORTED_CURRENCIES
            if current.upper() in currency
        ]
    
    @convert.autocomplete("to_currency")
    async def to_currency_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for to_currency parameter."""
        return [
            app_commands.Choice(name=currency, value=currency)
            for currency in self.SUPPORTED_CURRENCIES
            if current.upper() in currency
        ]


async def setup(bot: commands.Bot):
    """
    Setup function to add this cog to the bot.
    
    Args:
        bot: The Discord bot instance
    """
    await bot.add_cog(CurrencyConverter(bot))
