"""
Visualization service for generating graphs and charts.
"""

import io
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import Dict, List, Tuple

class VisualizationService:
    """
    Service for generating statistical visualizations.
    """
    def __init__(self):
        # Set style to dark background for Discord integration
        plt.style.use('dark_background')
        
    def generate_activity_heatmap(self, data: List[List[int]]) -> io.BytesIO:
        """
        Generate a heatmap of user activity.
        
        Args:
            data: 7x24 matrix of activity counts (7 days, 24 hours)
            
        Returns:
            io.BytesIO: Image buffer containing the heatmap
        """
        plt.figure(figsize=(10, 6))
        
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        sns.heatmap(data, cmap="viridis", cbar=True, yticklabels=days)
        plt.title("Activity Heatmap")
        plt.xlabel("Hour of Day")
        plt.ylabel("Day of Week")
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', facecolor='#2f3136')
        buf.seek(0)
        plt.close()
        return buf

    def generate_emoji_pie_chart(self, emoji_data: Dict[str, int]) -> io.BytesIO:
        """
        Generate a pie chart of top emojis.
        
        Args:
            emoji_data: Dictionary of emoji counts
            
        Returns:
            io.BytesIO: Image buffer containing the pie chart
        """
        # Sort and take top 10
        sorted_data = sorted(emoji_data.items(), key=lambda x: x[1], reverse=True)[:10]
        labels = [x[0] for x in sorted_data]
        sizes = [x[1] for x in sorted_data]
        
        plt.figure(figsize=(8, 8))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        plt.title("Top Emoji Usage")
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', facecolor='#2f3136')
        buf.seek(0)
        plt.close()
        return buf

    def generate_spam_stats_chart(self, spam_data: Dict[str, int]) -> io.BytesIO:
        """
        Generate a bar chart of spam types.
        
        Args:
            spam_data: Dictionary of spam type counts
            
        Returns:
            io.BytesIO: Image buffer
        """
        labels = list(spam_data.keys())
        values = list(spam_data.values())
        
        plt.figure(figsize=(10, 6))
        sns.barplot(x=labels, y=values, palette="rocket")
        plt.title("Spam Detection Statistics")
        plt.xlabel("Spam Type")
        plt.ylabel("Count")
        plt.xticks(rotation=45)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', facecolor='#2f3136')
        buf.seek(0)
        plt.close()
        return buf
