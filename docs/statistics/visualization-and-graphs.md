# Visualization and Graph Generation Plan

## Overview
This feature generates visual graphs and charts for user statistics (emoji usage, call times, spam analysis) directly on the server. These images are then embedded in Discord messages, providing a rich visual representation of the data.

## Requirements

### Graph Types
1. **Activity Heatmap**:
   - X-axis: Hour of day (0-23)
   - Y-axis: Day of week (Mon-Sun)
   - Color intensity: Activity level (message count or call duration)
2. **Trend Line Chart**:
   - Activity over time (last 7 days / 30 days)
3. **Pie/Donut Chart**:
   - Emoji usage distribution (Top 10 emojis)
   - Spam type distribution
4. **Bar Chart**:
   - Call duration per day

### Technical Requirements
- **Library**: `matplotlib` or `seaborn` (for static images)
- **Output**: PNG images stored in a temporary buffer (BytesIO)
- **Theme**: Dark mode style to match Discord's UI (dark background, light text)

## Implementation Details

### Visualization Service
Create a `VisualizationService` class in `utils/visualization.py`:

```python
import matplotlib.pyplot as plt
import seaborn as sns
import io

class VisualizationService:
    def __init__(self):
        # Set style
        plt.style.use('dark_background')
        
    def generate_activity_heatmap(self, data) -> io.BytesIO:
        """
        Generate a heatmap of user activity.
        data: Matrix of 7x24 values
        """
        plt.figure(figsize=(10, 6))
        sns.heatmap(data, cmap="viridis", cbar=True)
        plt.title("Activity Heatmap")
        plt.xlabel("Hour of Day")
        plt.ylabel("Day of Week")
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close()
        return buf

    def generate_emoji_pie_chart(self, emoji_data: dict) -> io.BytesIO:
        """
        Generate a pie chart of top emojis.
        """
        labels = list(emoji_data.keys())
        sizes = list(emoji_data.values())
        
        plt.figure(figsize=(8, 8))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        plt.title("Top Emoji Usage")
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close()
        return buf
```

### Integration with Commands

Update stats commands to include the generated image:

```python
@commands.command(name="graph")
async def show_graph(self, ctx, graph_type: str = "activity"):
    """
    Display a statistical graph.
    """
    # Fetch data
    data = await self.stats_service.get_activity_data(ctx.author.id)
    
    # Generate image
    image_buffer = self.viz_service.generate_activity_heatmap(data)
    
    # Send as file
    file = discord.File(image_buffer, filename="heatmap.png")
    embed = discord.Embed(title="Activity Heatmap")
    embed.set_image(url="attachment://heatmap.png")
    
    await ctx.send(embed=embed, file=file)
```

## Styling
- **Background**: `#2f3136` (Discord dark gray)
- **Text Color**: `#dcddde` (Discord text)
- **Palette**: Use a colorblind-friendly palette (e.g., Viridis or specialized categorical palettes)

## Performance
- **Blocking Operations**: Plotting can be slow. Run generation in a thread pool or separate process to avoid blocking the bot's event loop.
  ```python
  import asyncio
  
  # In command
  image_buffer = await asyncio.to_thread(self.viz_service.generate_activity_heatmap, data)
  ```

## Dependencies
```
matplotlib>=3.5.0
seaborn>=0.11.0
pandas>=1.3.0 (optional, for easier data manipulation)
```

## Future Enhancements
- Interactive graphs (using a web dashboard instead of static images)
- Comparison graphs (User vs Server Average)

---
*Plan created on 2025-11-25*
