# bioDYM repo
This project offers a use case for dynamic Material Flow Analysis (dMFA) in the field of organic waste management. It is based on the [ODYM framework](https://github.com/IndEcol/ODYM). The bioDYM project presents studies that apply dMFA with the ODYM framework. Also, additional features were  developed that include:

- Interactive Sankey diagrams
- Interactive stock plots
- Modelling first order processes (e.g. carbon mineralization in soil)
- Monte Carlo Simulation


# Recommended workflow
If you are interested in working with this project, you can proceed like this:

1. Download the repository, install all dependencies and access the repository with Jupyter Lab (more information in the installation folder).
2. Look through the basic_examples and studies Notebooks to understand what has been done and how. The workflow diagram and the explanations in the docs folder can be helpful.
3. Define what you want to do in your MFA and compare with what has been done in the studies.
4. Start to build your own Notebook step-by-step. Many code blocks can easily be copied and modified to fit the new study. The framework is rigid in the sense of transferability and comparability between different use cases. At the same time its flexibility allows adapting and even extending the procedures to fit your modelling needs. 

**If you need more information regarding ODYM or more modelling examples, check out the github page of the [ODYM framework](https://github.com/IndEcol/ODYM).**



# Repo folder structure

### basic_examples
1. **basic_example_1**:
Here you can learn about the basic data structure of ODYM and also about some of the additional features I developed for bioDYM. It shows a simple example system for a biomass MFA for a few years, tracking biomass and carbon using transfer coefficients.

*files included:*
- Modelling Notebook
- Input data file xlsx
- Case study results export xlsx
- By hand calculations for comparison xlsx


2. **basic_example_2**:
This MFA is very similar to the basic_example_1, but instead uses carbon content parameters instead of transfer coefficients. It basically models the harvesting process of wheat in a very simplified way.

*files included:*
- Modelling Notebook
- Input data file xlsx
- Case study results export xlsx
- By hand calculations for comparison xlsx

-----
### docs
Helpful resources for working with the project.

*files included:*
- workflow_diagram.pdf
- workflow_explained.pdf

-----
### framework
This folder includes a copy of the ODYM framework (ver. as of 27.11.2024) as well as the bioDYM add-on modules.

-----
### installation
Here you can find the requirements.txt file and resources for a reproducible workflow with Anaconda or Docker.

*files included:*
- requirements.txt
- Anaconda environment file
- Dockerfile (including a short introduction and installation commands)

----
### studies
The bioDYM project includes two studies of dMFA in organic waste management:

1. **rye_straw_cascading_treatment_system**:
This study is very cool because the data used for the model is based on a **research biogas plant from the chair of circular economy and recycling technology, TU Berlin**! The model presents a cascading treatment system for rye straw, including biogas production and mycelium-based composites (MBC) manufacturing. Dynamic stock modelling to account for different lifetimes of the MBC products is included. The EoL-Treatment of MBC products leads to the production of biochar to be used for soil enhancement. Carbon mineralization in the litosphere is taken into account via a first order model. 

*files included:*
- Modelling Notebook
- Input data file xlsx
- Case study results export xlsx
- By hand calculations for comparison xlsx
- Mass balance check for comparison xlsx


  
2. **case_study_bachelor_thesis**:
This is a case study I developed for my bachelor thesis using **hypothetical data**. It includes a Monte Carlo Simulation and modelling a first-order soil mineralization process. The system includes agricultural wheat production, subsequent treatment of residues (wheat straw) and the effect on atmosphere, surface water and aquifer and soil. The aim was devloping a model that allows obtaining information on the impact of applying agricultural residue treatment products as soil conditioner on the carbon stock of the soil. Since I used hypothetical data here, the workflow is what matters and not the resulting numbers.

*files included:*
- Modelling Notebook
- Input data file xlsx
- Case study results export xlsx
- Monte Carlo Simulation results export xlsx
- By hand calculations for comparison xlsx


  

