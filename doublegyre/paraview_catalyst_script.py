# script-version: 2.0
# Catalyst state generated using paraview version 6.1.0
import paraview
paraview.compatibility.major = 6
paraview.compatibility.minor = 1

#### import the simple module from the paraview
from paraview.simple import *
#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

# ----------------------------------------------------------------
# setup views used in the visualization
# ----------------------------------------------------------------

# Create a new 'Render View'
renderView1 = CreateView('RenderView')
renderView1.Set(
    ViewSize=[1164, 625],
    OrientationAxesVisibility=0,
    CenterOfRotation=[0.9959283447824419, 0.49609315814450383, 0.0],
    CameraPosition=[0.9959283447824419, 0.49609315814450383, 4.331848123013008],
    CameraFocalPoint=[0.9959283447824419, 0.49609315814450383, 0.0],
    CameraViewAngle=15.463917525773196,
)

# init the 'Grid Axes 3D Actor' selected for 'AxesGrid'
renderView1.AxesGrid.Visibility = 1

# ----------------------------------------------------------------
# setup the data processing pipelines
# ----------------------------------------------------------------

# create a new 'XML Image Data Reader'
grid = TrivialProducer(registrationName='grid')
grid.PointArrayStatus = ['Velocity']

# create a new 'Calculator'
add_z_component = Calculator(registrationName='add_z_component', Input=grid)
add_z_component.Set(
    ResultArrayName='velocity',
    Function='Velocity_X * iHat + Velocity_Y * jHat + 0 * kHat',
)

# create a new 'Glyph'
vector_field = Glyph(registrationName='vector_field', Input=add_z_component,
    GlyphType='Arrow')
vector_field.Set(
    OrientationArray=['POINTS', 'velocity'],
    ScaleArray=['POINTS', 'velocity'],
    ScaleFactor=0.2,
    GlyphMode='Uniform Spatial Distribution (Surface Sampling)',
    MaximumNumberOfSamplePoints=2500,
    Seed=1326,
)

# ----------------------------------------------------------------
# setup the visualization in view 'renderView1'
# ----------------------------------------------------------------

# show data from vector_field
vector_fieldDisplay = Show(vector_field, renderView1, 'GeometryRepresentation')

# get color transfer function/color map for 'Velocity'
velocityLUT = GetColorTransferFunction('Velocity')
velocityLUT.Set(
    RGBPoints=GenerateRGBPoints(
        range_min=0.004398556066774297,
        range_max=0.3228328036545508,
    ),
    ScalarRangeInitialized=1.0,
)

# trace defaults for the display properties.
vector_fieldDisplay.Set(
    Representation='Surface',
    ColorArrayName=['POINTS', 'Velocity'],
    LookupTable=velocityLUT,
)

# init the 'Piecewise Function' selected for 'ScaleTransferFunction'
vector_fieldDisplay.ScaleTransferFunction.Points = [-0.31415196052022276, 0.0, 0.5, 0.0, 0.31415228653854377, 1.0, 0.5, 0.0]

# init the 'Piecewise Function' selected for 'OpacityTransferFunction'
vector_fieldDisplay.OpacityTransferFunction.Points = [-0.31415196052022276, 0.0, 0.5, 0.0, 0.31415228653854377, 1.0, 0.5, 0.0]

# ----------------------------------------------------------------
# setup color maps and opacity maps used in the visualization
# note: the Get..() functions create a new object, if needed
# ----------------------------------------------------------------

# get opacity transfer function/opacity map for 'Velocity'
velocityPWF = GetOpacityTransferFunction('Velocity')
velocityPWF.Set(
    Points=[0.004398556066774297, 0.0, 0.5, 0.0, 0.3228328036545508, 1.0, 0.5, 0.0],
    ScalarRangeInitialized=1,
)

# ----------------------------------------------------------------
# setup extractors
# ----------------------------------------------------------------

# create extractor
pNG1 = CreateExtractor('PNG', renderView1, registrationName='PNG1')
# trace defaults for the extractor.
# init the 'Time Step' selected for 'Trigger'
pNG1.Trigger.Frequency = 10

# init the 'PNG' selected for 'Writer'
pNG1.Writer.Set(
    FileName='vector_field-{timestep:06d}.png',
    ImageResolution=[1164, 625],
    Format='PNG',
)

# ------------------------------------------------------------------------------
# Catalyst options
from paraview import catalyst
options = catalyst.Options()

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    from paraview.simple import SaveExtractsUsingCatalystOptions
    # Code for non in-situ environments; if executing in post-processing
    # i.e. non-Catalyst mode, let's generate extracts using Catalyst options
    SaveExtractsUsingCatalystOptions(options)
