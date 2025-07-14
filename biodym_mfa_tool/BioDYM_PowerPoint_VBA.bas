Sub CreateBioDYMPresentation()
    ' BioDYM Material Flow Analysis Tool - PowerPoint Presentation Generator
    ' This VBA code creates a professional 4-slide presentation about the BioDYM tool
    
    Dim pptApp As PowerPoint.Application
    Dim pptPres As PowerPoint.Presentation
    Dim pptSlide As PowerPoint.Slide
    Dim pptShape As PowerPoint.Shape
    
    ' Set up PowerPoint application
    Set pptApp = Application
    Set pptPres = pptApp.ActivePresentation
    
    ' Clear existing slides (optional - comment out if you want to keep existing slides)
    ' While pptPres.Slides.Count > 0
    '     pptPres.Slides(1).Delete
    ' Wend
    
    ' ========================================
    ' SLIDE 1: Tool Overview & Structure
    ' ========================================
    Set pptSlide = pptPres.Slides.Add(pptPres.Slides.Count + 1, ppLayoutText)
    
    ' Title
    pptSlide.Shapes(1).TextFrame.TextRange.Text = "BioDYM Material Flow Analysis Tool"
    pptSlide.Shapes(1).TextFrame.TextRange.Font.Size = 44
    pptSlide.Shapes(1).TextFrame.TextRange.Font.Bold = True
    pptSlide.Shapes(1).TextFrame.TextRange.Font.Color = RGB(0, 51, 102)
    
    ' Subtitle
    pptSlide.Shapes(2).TextFrame.TextRange.Text = "Advanced Material Flow Analysis for Biomass Systems"
    pptSlide.Shapes(2).TextFrame.TextRange.Font.Size = 24
    pptSlide.Shapes(2).TextFrame.TextRange.Font.Color = RGB(51, 102, 153)
    
    ' Add content box
    Set pptShape = pptSlide.Shapes.AddTextBox(1, 50, 200, 600, 400)
    pptShape.TextFrame.TextRange.Text = "What is BioDYM?" & vbCrLf & vbCrLf & _
        "• Material Flow Analysis (MFA) tool for biomass and organic material systems" & vbCrLf & _
        "• Built on the ODYM framework with custom BioDYM extensions" & vbCrLf & _
        "• Designed for scientific research and policy analysis" & vbCrLf & vbCrLf & _
        "Tool Structure:" & vbCrLf & _
        "• Excel Interface: User-friendly data input via structured Excel sheets" & vbCrLf & _
        "• Calculation Engine: Advanced MFA algorithms with Monte Carlo simulation" & vbCrLf & _
        "• Visualization Suite: Interactive plots, Sankey diagrams, and analysis tools" & vbCrLf & _
        "• Export System: Comprehensive results in Excel and image formats"
    
    pptShape.TextFrame.TextRange.Font.Size = 18
    pptShape.TextFrame.TextRange.Font.Color = RGB(0, 0, 0)
    
    ' Add key innovation box
    Set pptShape = pptSlide.Shapes.AddTextBox(1, 50, 620, 600, 100)
    pptShape.TextFrame.TextRange.Text = "Key Innovation:" & vbCrLf & _
        "Excel Interface + Python Power = Scientific Rigor"
    pptShape.TextFrame.TextRange.Font.Size = 20
    pptShape.TextFrame.TextRange.Font.Bold = True
    pptShape.TextFrame.TextRange.Font.Color = RGB(0, 102, 0)
    pptShape.Fill.ForeColor.RGB = RGB(240, 248, 255)
    pptShape.Line.ForeColor.RGB = RGB(0, 102, 0)
    
    ' ========================================
    ' SLIDE 2: Data Input & Configuration
    ' ========================================
    Set pptSlide = pptPres.Slides.Add(pptPres.Slides.Count + 1, ppLayoutText)
    
    ' Title
    pptSlide.Shapes(1).TextFrame.TextRange.Text = "Excel-Based Data Input System"
    pptSlide.Shapes(1).TextFrame.TextRange.Font.Size = 44
    pptSlide.Shapes(1).TextFrame.TextRange.Font.Bold = True
    pptSlide.Shapes(1).TextFrame.TextRange.Font.Color = RGB(0, 51, 102)
    
    ' Add main content
    Set pptShape = pptSlide.Shapes.AddTextBox(1, 50, 150, 300, 500)
    pptShape.TextFrame.TextRange.Text = "Input Structure:" & vbCrLf & vbCrLf & _
        "• 20+ organized Excel sheets for different data types" & vbCrLf & _
        "• Standardized format for easy data entry and validation" & vbCrLf & _
        "• Configuration-driven approach for flexibility" & vbCrLf & vbCrLf & _
        "Main Data Categories:" & vbCrLf & vbCrLf & _
        "1. System Definition" & vbCrLf & _
        "   • Process definitions (cultivation, processing, utilization)" & vbCrLf & _
        "   • Flow definitions (material transfers between processes)" & vbCrLf & _
        "   • Stock definitions (material accumulation over time)" & vbCrLf & vbCrLf & _
        "2. Parameter Data" & vbCrLf & _
        "   • Transfer coefficients (material flow rates)" & vbCrLf & _
        "   • Dynamic parameters (time-varying coefficients)" & vbCrLf & _
        "   • Initial stock values (starting conditions)"
    
    pptShape.TextFrame.TextRange.Font.Size = 16
    pptShape.TextFrame.TextRange.Font.Color = RGB(0, 0, 0)
    
    ' Add right side content
    Set pptShape = pptSlide.Shapes.AddTextBox(1, 380, 150, 300, 500)
    pptShape.TextFrame.TextRange.Text = "3. Advanced Models" & vbCrLf & _
        "   • DSM (Dynamic Stock Model): Lifetime-based material flows" & vbCrLf & _
        "   • FOMP (First-Order Mineralization Process): Organic matter decay" & vbCrLf & _
        "   • Monte Carlo: Uncertainty analysis with 6+ parameter types" & vbCrLf & vbCrLf & _
        "4. Configuration" & vbCrLf & _
        "   • Time period settings (2025-2050)" & vbCrLf & _
        "   • Element definitions (material, WC, DM, CC)" & vbCrLf & _
        "   • Analysis options (iterations, thresholds, export formats)" & vbCrLf & vbCrLf & _
        "User Experience:" & vbCrLf & _
        "✅ No programming required - pure Excel interface" & vbCrLf & _
        "✅ Structured templates - guided data entry" & vbCrLf & _
        "✅ Validation system - automatic error checking" & vbCrLf & _
        "✅ Flexible configuration - adaptable to different systems"
    
    pptShape.TextFrame.TextRange.Font.Size = 16
    pptShape.TextFrame.TextRange.Font.Color = RGB(0, 0, 0)
    
    ' ========================================
    ' SLIDE 3: Core Functions & Analysis
    ' ========================================
    Set pptSlide = pptPres.Slides.Add(pptPres.Slides.Count + 1, ppLayoutText)
    
    ' Title
    pptSlide.Shapes(1).TextFrame.TextRange.Text = "Core Functions & Analysis Capabilities"
    pptSlide.Shapes(1).TextFrame.TextRange.Font.Size = 44
    pptSlide.Shapes(1).TextFrame.TextRange.Font.Bold = True
    pptSlide.Shapes(1).TextFrame.TextRange.Font.Color = RGB(0, 51, 102)
    
    ' Add left column
    Set pptShape = pptSlide.Shapes.AddTextBox(1, 50, 150, 300, 500)
    pptShape.TextFrame.TextRange.Text = "1. Material Flow Calculation" & vbCrLf & vbCrLf & _
        "• Mass balance verification across all processes" & vbCrLf & _
        "• Multi-element analysis (material, water content, dry matter, carbon content)" & vbCrLf & _
        "• Time-series modeling (annual calculations over 25+ years)" & vbCrLf & _
        "• Stock evolution tracking and prediction" & vbCrLf & vbCrLf & _
        "2. Advanced Modeling" & vbCrLf & vbCrLf & _
        "Dynamic Stock Model (DSM):" & vbCrLf & _
        "• Material lifetime analysis" & vbCrLf & _
        "• Category tracking (Blech, Eisen, Stahl, Wolle)" & vbCrLf & _
        "• Lifetime-based outflow predictions" & vbCrLf & vbCrLf & _
        "First-Order Mineralization Process (FOMP):" & vbCrLf & _
        "• Organic matter decay modeling" & vbCrLf & _
        "• Cumulative mineralization tracking" & vbCrLf & _
        "• Long-term organic matter stock prediction"
    
    pptShape.TextFrame.TextRange.Font.Size = 16
    pptShape.TextFrame.TextRange.Font.Color = RGB(0, 0, 0)
    
    ' Add right column
    Set pptShape = pptSlide.Shapes.AddTextBox(1, 380, 150, 300, 500)
    pptShape.TextFrame.TextRange.Text = "3. Uncertainty Analysis (Monte Carlo)" & vbCrLf & vbCrLf & _
        "• 6+ parameter types for uncertainty modeling" & vbCrLf & _
        "• Configurable iterations (10-1000+ runs)" & vbCrLf & _
        "• Distribution analysis (uniform, normal distributions)" & vbCrLf & _
        "• Sensitivity analysis and confidence intervals" & vbCrLf & vbCrLf & _
        "4. Validation & Quality Control" & vbCrLf & vbCrLf & _
        "• Mass balance verification with tolerance settings" & vbCrLf & _
        "• Data validation with automatic error detection" & vbCrLf & _
        "• Consistency checks across all system components" & vbCrLf & _
        "• Quality indicators for result reliability" & vbCrLf & vbCrLf & _
        "Analysis Pipeline:" & vbCrLf & _
        "📊 Input Data → 🧮 Calculation → 📈 Visualization → 📤 Export"
    
    pptShape.TextFrame.TextRange.Font.Size = 16
    pptShape.TextFrame.TextRange.Font.Color = RGB(0, 0, 0)
    
    ' ========================================
    ' SLIDE 4: Visualization & Scientific Applications
    ' ========================================
    Set pptSlide = pptPres.Slides.Add(pptPres.Slides.Count + 1, ppLayoutText)
    
    ' Title
    pptSlide.Shapes(1).TextFrame.TextRange.Text = "Visualization & Scientific Applications"
    pptSlide.Shapes(1).TextFrame.TextRange.Font.Size = 44
    pptSlide.Shapes(1).TextFrame.TextRange.Font.Bold = True
    pptSlide.Shapes(1).TextFrame.TextRange.Font.Color = RGB(0, 51, 102)
    
    ' Add left column - Visualization
    Set pptShape = pptSlide.Shapes.AddTextBox(1, 50, 150, 300, 500)
    pptShape.TextFrame.TextRange.Text = "Comprehensive Visualization Suite:" & vbCrLf & vbCrLf & _
        "System Overview Visualizations:" & vbCrLf & _
        "• Interactive Sankey Diagrams: Material flow visualization" & vbCrLf & _
        "• Stock Bar Charts: Process-wise stock analysis" & vbCrLf & _
        "• Multi-process selection and filtering" & vbCrLf & vbCrLf & _
        "Detailed Analysis Plots:" & vbCrLf & _
        "• Individual Process Analysis: 3-panel layout" & vbCrLf & _
        "• DSM Analysis: Lifetime-based modeling" & vbCrLf & _
        "• FOMP Analysis: Organic matter dynamics" & vbCrLf & vbCrLf & _
        "Monte Carlo Results:" & vbCrLf & _
        "• Distribution Analysis: Parameter uncertainty visualization" & vbCrLf & _
        "• Correlation Matrices: Parameter relationship analysis" & vbCrLf & _
        "• Confidence Intervals: Uncertainty quantification" & vbCrLf & _
        "• Integrated Dashboard: 4-panel comprehensive view"
    
    pptShape.TextFrame.TextRange.Font.Size = 16
    pptShape.TextFrame.TextRange.Font.Color = RGB(0, 0, 0)
    
    ' Add right column - Applications
    Set pptShape = pptSlide.Shapes.AddTextBox(1, 380, 150, 300, 500)
    pptShape.TextFrame.TextRange.Text = "Scientific Applications:" & vbCrLf & vbCrLf & _
        "Target Research Areas:" & vbCrLf & _
        "• Biomass utilization and cascading systems" & vbCrLf & _
        "• Organic waste management and circular economy" & vbCrLf & _
        "• Agricultural systems and crop residue management" & vbCrLf & _
        "• Policy analysis and scenario modeling" & vbCrLf & vbCrLf & _
        "Scientific Benefits:" & vbCrLf & _
        "• Reproducible analysis with standardized methodology" & vbCrLf & _
        "• Uncertainty quantification for robust conclusions" & vbCrLf & _
        "• Multi-scale analysis from process to system level" & vbCrLf & _
        "• Scenario comparison for policy decision support" & vbCrLf & vbCrLf & _
        "Output Quality:" & vbCrLf & _
        "• Peer-review ready results and visualizations" & vbCrLf & _
        "• Comprehensive documentation of methodology" & vbCrLf & _
        "• Uncertainty analysis for robust conclusions" & vbCrLf & _
        "• Export flexibility for different publication formats"
    
    pptShape.TextFrame.TextRange.Font.Size = 16
    pptShape.TextFrame.TextRange.Font.Color = RGB(0, 0, 0)
    
    ' Add conclusion box at bottom
    Set pptShape = pptSlide.Shapes.AddTextBox(1, 50, 680, 630, 80)
    pptShape.TextFrame.TextRange.Text = "Key Message: BioDYM empowers researchers to conduct sophisticated material flow analysis without requiring programming expertise, while providing the depth and rigor needed for high-quality scientific research."
    pptShape.TextFrame.TextRange.Font.Size = 18
    pptShape.TextFrame.TextRange.Font.Bold = True
    pptShape.TextFrame.TextRange.Font.Color = RGB(0, 102, 0)
    pptShape.Fill.ForeColor.RGB = RGB(240, 248, 255)
    pptShape.Line.ForeColor.RGB = RGB(0, 102, 0)
    
    ' Apply consistent formatting to all slides
    ApplyConsistentFormatting pptPres
    
    MsgBox "BioDYM presentation created successfully! 4 slides have been added to your presentation.", vbInformation, "Presentation Complete"
    
End Sub

Sub ApplyConsistentFormatting(pptPres As PowerPoint.Presentation)
    ' Apply consistent formatting to all slides
    Dim pptSlide As PowerPoint.Slide
    Dim pptShape As PowerPoint.Shape
    
    For Each pptSlide In pptPres.Slides
        ' Apply background color
        pptSlide.Background.Fill.ForeColor.RGB = RGB(255, 255, 255)
        
        ' Format all text boxes
        For Each pptShape In pptSlide.Shapes
            If pptShape.HasTextFrame Then
                ' Set consistent font
                pptShape.TextFrame.TextRange.Font.Name = "Calibri"
                
                ' Apply bullet formatting where appropriate
                If InStr(pptShape.TextFrame.TextRange.Text, "•") > 0 Then
                    pptShape.TextFrame.TextRange.ParagraphFormat.Bullet = True
                    pptShape.TextFrame.TextRange.ParagraphFormat.Bullet.Font.Name = "Calibri"
                    pptShape.TextFrame.TextRange.ParagraphFormat.Bullet.Font.Size = 16
                End If
            End If
        Next pptShape
    Next pptSlide
End Sub

Sub AddSlideNumbers()
    ' Add slide numbers to all slides
    Dim pptSlide As PowerPoint.Slide
    Dim pptShape As PowerPoint.Shape
    Dim slideNumber As Integer
    
    slideNumber = 1
    
    For Each pptSlide In ActivePresentation.Slides
        ' Add slide number at bottom right
        Set pptShape = pptSlide.Shapes.AddTextBox(1, 650, 700, 100, 30)
        pptShape.TextFrame.TextRange.Text = "Slide " & slideNumber
        pptShape.TextFrame.TextRange.Font.Size = 12
        pptShape.TextFrame.TextRange.Font.Color = RGB(128, 128, 128)
        pptShape.TextFrame.TextRange.Font.Italic = True
        
        slideNumber = slideNumber + 1
    Next pptSlide
End Sub

Sub AddCompanyLogo()
    ' Add company logo placeholder (you can replace with actual logo)
    Dim pptSlide As PowerPoint.Slide
    Dim pptShape As PowerPoint.Shape
    
    For Each pptSlide In ActivePresentation.Slides
        ' Add logo placeholder at top right
        Set pptShape = pptSlide.Shapes.AddTextBox(1, 650, 20, 100, 40)
        pptShape.TextFrame.TextRange.Text = "BioDYM"
        pptShape.TextFrame.TextRange.Font.Size = 14
        pptShape.TextFrame.TextRange.Font.Bold = True
        pptShape.TextFrame.TextRange.Font.Color = RGB(0, 51, 102)
        pptShape.Fill.ForeColor.RGB = RGB(240, 248, 255)
        pptShape.Line.ForeColor.RGB = RGB(0, 51, 102)
    Next pptSlide
End Sub

' ========================================
' USAGE INSTRUCTIONS:
' ========================================
' 1. Open PowerPoint
' 2. Press Alt + F11 to open VBA editor
' 3. Insert a new module (Insert > Module)
' 4. Copy and paste this code into the module
' 5. Press F5 or run the "CreateBioDYMPresentation" macro
' 6. The presentation will be created with 4 professional slides
' 7. Optional: Run "AddSlideNumbers" and "AddCompanyLogo" for additional formatting
'
' FEATURES:
' - Professional color scheme (navy blue and green)
' - Consistent formatting across all slides
' - Bullet points and structured content
' - Highlighted key messages
' - Ready for presentation
' ======================================== 