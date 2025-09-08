2.3.	Case Studies to show application of BioDYM
The following two case studies are designed to demonstrate the application of BioDYM for dynamic carbon cycle assessment in complex biogenic material systems. Basis for the carbon cycle assessment is the assumption that all components of the biogenic substances are received either from the Atmosphere (P0) or from the Environment (P1). The atmosphere is the major source for biogenic carbon, through the transformation of CO2 into biomass by photosynthesis. Every other component of the biomass is aggregated into a single environmental flow, originating in the environment, consisting mainly of water and other nutrients. Water and nutrients are part of the water and nutrient cycle. For the scope of the study, the atmosphere and the environment form stocks, with an unlimited supply of material. This assumption is justified with the focus on carbon flows, with the objective to model the carbon uptake of the system. 
Case Study 1: Carbon cycles within the wheat straw economy
Objectives:
Case study 1 (CS1) describes harvest, utilization and EoL treatment of wheat straw resulting from agricultural processes. BioDYM is used to calculate carbon flows and to display dynamic carbon cycles. Specific objectives of CS 1 are:
	To quantify the annual and total carbon uptake from the atmosphere and the development of carbon stocks of the system based on dynamic input data. 
	To evaluate the impact of a shift in technology over time with different treatment scenarios. 
	To analyze first order mineralization processes and carbon uptake of the soil by composting rye straw. 
	To identify most critical parameters influencing the system through a Monte Carlo simulation.
Systemboundaries:
The system of CS 1 describes the entire lifecycle of wheat, starting with the raw material extraction, product manufacturing, use-phase and EoL-phase. The system is part of the global carbon cycle and includes the atmosphere and the lithosphere as global carbon stocks. The geographical scope is defined as a representative region in central Europe. The temporal boundary for the analysis covers 25 years, from 2025 to 2050, to incorporate future system dynamics based on historical data. 
Processes and flows
The model consists of 9 processes building one circular system. Every process is located within the system boundaries of the study and is connected with input and output flows with each other. This structure allows modelling cycles within the global carbon cycle. Table 1 contains an overview of all processes in the system, the process type and a description of the function. In addition, it is indicated, if an uncertainty is used for the MC simulation. 
Table 2: Process List case study 1
ID	Name	Type	Uncertainty	Function
P0	Atmosphere	Stock	No	Provides carbon for the cultivation of wheat.
P1	Environment	Stock	No	Provides all other supplements & water for the cultivation of wheat
P2	Cultivation	Process 	No	Cultivation of wheat
P3	Harvesting	Process; TC	No	Harvesting of wheat. Split of grains and straw
P4	Grain processing & Consumption	Process; TC	No	Processing wheat grains and consumption of resulting food.
P5	Straw collection/ distribution	Process (DynTC)	Yes (normal distribution)	Collection and distribution of wheat straw into several applications. Dynamic TCs model a shift in technology
P6	Incorporation	Process	No	Direct incorporation of straw residues into agricultural soil.
P7	Animal bedding	Process; TC	No	Use of straw as absorbent bedding material in livestock farming
P8 	Lithosphere	Stock; FOMP	Yes (normal distribution)	The soil as large carbon stock, including slow mineralization processes of carbon

Flows
Case study 1 is based on realistic data combined with assumptions with a highly explorative purpose. All flows are defined as product carbon or environmental flows. Each flow is treated as FM with the dimensions, WC, DM and CC. The detailed data sheets for CS 1 as well as the calculation model are available within the SI.
The quantity of harvested wheat is intended to describe a realistic scenario and the common best practice within the system boundaries. Straw input is material flow data about the annual yield (Yt) of wheat straw from 2025 -2050. Assumed is an agricultural area for wheat cultivation of 1000km² (100.000 ha) in Germany. As a yield for winter wheat in Germany 7.7 Mg/ ha with an annual fluctuation of +- 1.0 mg/ha are assumed (source). In addition, a long-term trend of 0.5% yield increase is included in the assumed flow. 

Y_t=Y_(trend,t)+∈_t			(1)
Y_(trend,t)=Y_base*(1+r_trend*(t-t_0 )) (2)
∈_t~N(0,σ_Y^2)
Yt final calculated yield for year t
Y_(trend,t) is the projected yield for year t based on a linear trend
∈_t = is the random fluctuation for year t to simulate natural variability 


Central for CS1 is the material composition of wheat straw at harvest status. The used data is based on laboratory experiments in combination with literature data. An overview of the material composition is visible in Table X. 
		Uncertainty parameters
Material Fraction	Value	Distribution type		
Fresh mass (FM)	100%	None		
Water content (WC)	14%	Triangular	Min= 10%	Max = 18%
Dry mass (DM)	86%	none		
Carbon Content of the DM	48%	Normal	Mean= 48%	Std. dev. =1%
Carbon Content of FM		None		
Transfer coefficients
Process transfer coefficients (TCs) determining the output flows of selected processes. The processes are based on the transformation principle of biogenic carbon. Transfer coefficients for the wheat harvest are based on a straw/ grain balance. Straw collection & distribution on DBFZ research data, describing the technical biomass potential for wheat straw in Germany (Source). All other TCs are based on illustrative assumptions detailed in the SI.
System diagram
Described information about processes, flows and systemboundaries are visible in Figure 1 System diagram for the wheat straw case study (CS1). Processes are shown as boxes, material flows as arrows, and the system boundary is delineated by the dashed line.
 

Figure 1: System diagram of CS1. 

Dynamic Stock Modeling (DSM):

irst-Order Mineralization Process (FOMP): You have correctly identified the Lithosphere (P8)

Dynamic Transfer Coefficients (DynTC)



	Uncertainty and Sensitivity Analysis Setup
This section describes the procedure of your Monte Carlo (MC) analysis, not just the uncertain parameters.
	Monte Carlo Simulation Setup: You should describe the simulation's execution. This includes:
	The number of simulation runs (e.g., "The model was run 1,000 times...").
	The Key Performance Indicators (KPIs) you tracked. What specific outputs did you record from each run to analyze the results? (e.g., "the total carbon stock in the lithosphere in the year 2050").
	Sensitivity Analysis Method: Your objectives state you will "simulate the sensitivity of critical processes." You should specify how you will do this. The most common method, which fits your setup, is to generate scatter plots of the uncertain input parameters against the final KPIs. Parameters that show a strong correlation or pattern are identified as the most sensitive.

