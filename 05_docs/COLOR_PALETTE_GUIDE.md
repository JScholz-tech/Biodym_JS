# 🎨 BioDYM Color Palette Guide

## 20 Recommended Colors for BioDYM System Visualization

### 🌱 **Biomass & Natural Colors**
| Color Name | Hex Code | RGB | Usage |
|------------|----------|-----|-------|
| Forest Green | `#228B22` | (34, 139, 34) | Primary biomass, organic matter |
| Olive Green | `#6B8E23` | (107, 142, 35) | Secondary biomass, plant material |
| Sage Green | `#9CAF88` | (156, 175, 136) | Processed biomass, compost |
| Earth Brown | `#8B4513` | (139, 69, 19) | Soil, organic matter |
| Wheat Gold | `#F5DEB3` | (245, 222, 179) | Straw, agricultural waste |

### 💧 **Water & Liquid Colors**
| Color Name | Hex Code | RGB | Usage |
|------------|----------|-----|-------|
| Ocean Blue | `#0066CC` | (0, 102, 204) | Water content, liquid flows |
| Aqua Blue | `#00CED1` | (0, 206, 209) | Process water, treatment |
| Deep Blue | `#191970` | (25, 25, 112) | Deep water, storage |
| Light Blue | `#87CEEB` | (135, 206, 235) | Water vapor, evaporation |

### 🔥 **Energy & Processing Colors**
| Color Name | Hex Code | RGB | Usage |
|------------|----------|-----|-------|
| Fire Orange | `#FF4500` | (255, 69, 0) | Energy, heat, combustion |
| Amber | `#FFBF00` | (255, 191, 0) | Energy storage, power |
| Red Orange | `#FF6347` | (255, 99, 71) | High energy processes |
| Dark Red | `#8B0000` | (139, 0, 0) | Waste, losses, emissions |

### ♻️ **Recycling & Circular Colors**
| Color Name | Hex Code | RGB | Usage |
|------------|----------|-----|-------|
| Teal | `#008B8B` | (0, 139, 139) | Recycling processes |
| Mint Green | `#98FB98` | (152, 251, 152) | Circular flows, reuse |
| Purple | `#9370DB` | (147, 112, 219) | Circular economy processes |
| Indigo | `#4B0082` | (75, 0, 130) | Advanced recycling |

### 📊 **System & Flow Colors**
| Color Name | Hex Code | RGB | Usage |
|------------|----------|-----|-------|
| Steel Blue | `#4682B4` | (70, 130, 180) | System processes |
| Slate Gray | `#708090` | (112, 128, 144) | Infrastructure, storage |
| Dark Gray | `#2F4F4F` | (47, 79, 79) | System boundaries |
| Silver | `#C0C0C0` | (192, 192, 192) | Neutral processes |

## 🎯 **Recommended Color Schemes for Different System Types**

### **Agricultural Biomass System**
```
Primary Input: #228B22 (Forest Green)
Processing: #4682B4 (Steel Blue)
Water Content: #0066CC (Ocean Blue)
Output: #F5DEB3 (Wheat Gold)
Recycling: #98FB98 (Mint Green)
```

### **Circular Economy System**
```
Input: #228B22 (Forest Green)
Processing: #008B8B (Teal)
Recycling: #9370DB (Purple)
Output: #F5DEB3 (Wheat Gold)
Energy: #FF4500 (Fire Orange)
```

### **Water Treatment System**
```
Water Input: #0066CC (Ocean Blue)
Treatment: #00CED1 (Aqua Blue)
Storage: #191970 (Deep Blue)
Output: #87CEEB (Light Blue)
Waste: #8B0000 (Dark Red)
```

## 📋 **Color Usage Guidelines**

### **Process Types**
- **Input Processes**: Green tones (#228B22, #6B8E23)
- **Processing**: Blue tones (#4682B4, #008B8B)
- **Circular/Recycling**: Purple/Teal tones (#9370DB, #008B8B)
- **Output**: Gold/Yellow tones (#F5DEB3, #FFBF00)
- **Waste/Losses**: Red tones (#8B0000, #FF6347)

### **Flow Types**
- **Material Flows**: Green/Blue tones
- **Water Flows**: Blue tones
- **Energy Flows**: Orange/Red tones
- **Recycling Flows**: Purple/Teal tones
- **Waste Flows**: Red/Gray tones

### **Element-Specific Colors**
- **Material (DM)**: #228B22 (Forest Green)
- **Water Content (WC)**: #0066CC (Ocean Blue)
- **Carbon Content (CC)**: #8B4513 (Earth Brown)
- **Ash Content**: #708090 (Slate Gray)

## 🎨 **Visual Hierarchy Tips**

1. **Use darker colors** for primary processes
2. **Use lighter colors** for secondary processes
3. **Use contrasting colors** for different flow types
4. **Use consistent colors** for similar process types
5. **Use muted colors** for background elements

## 📝 **Excel Configuration Example**

```excel
Process_Visualization:
Process_ID | Process_Name | Node_Color
P_01      | Input        | #228B22
P_02      | Processing   | #4682B4
P_03      | Recycling    | #9370DB
P_04      | Output       | #F5DEB3

Flow_Visualization:
Flow_ID | Flow_Name | Flow_Color
F_01_02 | Material  | #228B22
F_02_03 | Water     | #0066CC
F_03_02 | Recycling | #9370DB
F_02_04 | Output    | #F5DEB3
```

## 🔧 **Implementation in BioDYM**

To use these colors in your BioDYM system:

1. **Open** `data/01_input/BioDYM_Visualization_Config.xlsx`
2. **Edit** the `Process_Visualization` sheet
3. **Replace** the `Node_Color` values with your chosen colors
4. **Edit** the `Flow_Visualization` sheet
5. **Replace** the `Flow_Color` values with your chosen colors
6. **Save** the file and run your analysis

## 🎯 **Accessibility Considerations**

- **High contrast** between text and background
- **Colorblind-friendly** combinations
- **Consistent** color usage across all visualizations
- **Clear** distinction between different process types

## 📚 **Additional Resources**

- [Color Theory for Data Visualization](https://blog.datawrapper.de/colors/)
- [Accessible Color Palettes](https://colorbrewer2.org/)
- [Material Design Colors](https://material.io/design/color/)
