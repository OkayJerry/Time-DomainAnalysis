<h1 align="center">Time-Domain Analysis Software</h1>

![cCEIdwii8g](https://github.com/OkayJerry/Time-DomainAnalysis/assets/70593138/5df1a3e1-5fca-406a-8e0c-f25ec3c2e886)

<p align="center">
This software is designed to analyze EPICS (Experimental Physics and Industrial Control System) Process Variables (PVs). It provides tools for researchers and engineers working with EPICS data.
</p>

## Documentation
![Main Marked Up](https://github.com/OkayJerry/Time-DomainAnalysis/assets/70593138/dc63f378-dda4-4eed-9a30-08d80972f6e2)

### Basic Elements
1. **Sampling/Plotting Frequency** $\rightarrow$ Sample & plot PV data every $\dfrac{1}{x}$ seconds.
2. **Start/Stop Button** $\rightarrow$ Toggles sampling, calculations, & plotting.
3. **Add PV Button** $\rightarrow$ Adds a blank PV to the PV Editor's table.
4. **PV Name Line Edit** $\rightarrow$ Displays the name of the PV. It is editable, but duplicate names are not allowed.
5. **PV's Most Recent Sample Value**
6. **PV Color**
7. **PV Parameters Button** $\rightarrow$ Open the PV's parameter dialog window.
8. [PV Parameters Dialog](#pv-parameters-dialog) $\rightarrow$ Displays editable PV parameters.
9. **Data Point Slider** $\rightarrow$ Plot & calculate over $x$ of the most recent data points.

### PV Parameters Dialog
*Displays editable PV parameters.*

![PV Parameters Dialog Image](https://github.com/OkayJerry/Time-DomainAnalysis/assets/70593138/f7e37723-74a0-4b11-bce2-dcf3a9844391)<!-- .element style="text-align: left;" -->

- `Enable` $\rightarrow$ Whether to calculate & plot the parent line.
- `Original` $\rightarrow$ Plot the data as sampled.
- `Rolling Window` $\rightarrow$ Calculate & plot the average of a subset of adjacent samples within a moving window.
- `Exponentially Weighted` $\rightarrow$ Calculate & plot an average that assigns decreasing weights to previous samples. In other words, more importance is given to recent data points.
- `Adaptive Average` $\rightarrow$ Calculate & plot an average that dynamically adjusts to the characteristics of the data. This is especially useful to account for jumps in value.
- `Subplot ID` $\rightarrow$ Assign the line to a subplot.
- `Color` $\rightarrow$ Opens a color dialog for selecting a color.
- `Apply` $\rightarrow$ Applies any changes.
-  `Apply & OK` $\rightarrow$ Applies any changes and closes the dialog.

## How to Install
### Windows / MacOS
```
git clone https://github.com/OkayJerry/Time-DomainAnalysis.git
cd Time-DomainAnalysis
pip install -r requirements.txt
```

### Linux (Debian Bookworm)
```
git clone https://github.com/OkayJerry/Time-DomainAnalysis.git
sudo apt install python3-pyqt6
sudo apt install python3-pyqtgraph
```


