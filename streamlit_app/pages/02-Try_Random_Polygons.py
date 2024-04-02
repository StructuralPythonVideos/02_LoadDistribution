
import streamlit as st
from shapely import Polygon
from shapely.affinity import translate
import polygon_generator as gen
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as PolygonPatch
from papermodels.models import load_distribution as ld

# From https://stackoverflow.com/questions/8997099/algorithm-to-generate-random-2d-polygon/25276331#25276331

st.write("# Compare bending moments: Projected beam load vs. 'Smeared' beam load")

st.sidebar.write("## Random Polygon Generator")

with st.form("Polygon generator"):
    with st.sidebar:
        irregularity_slider = st.slider("Irregularity", min_value=0., max_value=1.0)
        spikiness_slider = st.slider("Spikiness", min_value=0., max_value=1.0)
        num_vertices_slider = st.slider("Number of vertices", min_value=4, max_value=30)
        test_poly_coords = st.form_submit_button(
            label="Generate polygon", 
            on_click=gen.generate_polygon, 
            kwargs=dict(
                center=(0, 0),
                avg_radius=60,
                irregularity=irregularity_slider,
                spikiness=spikiness_slider,
                num_vertices=num_vertices_slider
        ), 
        )

test_poly_coords = st.session_state.get('random_polygon_points')
if test_poly_coords is None:
    st.success("Begin by generating a polygon with the button...")
    st.stop()
test_poly_coords = st.session_state.get('random_polygon_points')

st.sidebar.write("---")
st.sidebar.write("## Apply load to polygon area")
total_load = st.sidebar.number_input(label="Total load of shape:", value=2000, step=10)
st.sidebar.write("---")

test_poly = Polygon(test_poly_coords)

xmin, ymin, xmax, ymax = test_poly.bounds
test_poly = translate(test_poly, xoff=-xmin, yoff=-ymin)
test_poly_coords = list(test_poly.exterior.coords)
xmin, ymin, xmax, ymax = test_poly.bounds

projected_poly = ld.project_polygon(test_poly, total_load=total_load)
projected_poly_xy = ld.project_polygon(test_poly, total_load=total_load, xy=True)
projected_poly_coords = list(zip(*projected_poly_xy))
xmin2, ymin2, xmax2, ymax2 = projected_poly.bounds

fig, (ax, ax2) = plt.subplots(nrows=2, ncols=1, sharex=True)
poly_patch = PolygonPatch(test_poly_coords)
ax.add_patch(poly_patch)

ax.set_xlim((-2, xmax - xmin +2))
ax.set_ylim((-2, ymax - ymin +2))
ax.set_title(label="Randomly Generated Polygon Representing an Irregular Load in the Trib Area")

projected_poly_patch = PolygonPatch(projected_poly.exterior.coords, fc="#55aa99", ec="#666")
l_side = xmin
l_tri_patch = PolygonPatch([[l_side, 0], [-2.5 + l_side, -5], [2.5 + l_side, -5]], fc=(0.5, 0.5, 0.5), ec='k')
r_side = xmax
r_tri_patch = PolygonPatch([[r_side, 0], [r_side-2.5, -5], [r_side+2.5, -5]], fc=(0.5, 0.5, 0.5), ec='k')
ax2.plot([xmin, xmax], [0, 0], 'k')
ax2.add_patch(l_tri_patch)
ax2.add_patch(r_tri_patch)
ax2.add_patch(projected_poly_patch)
for coord in projected_poly_coords:
    ax2.annotate(text=f"w={round(coord[1],1)};\nx={round(coord[0],1)}", xy=coord, fontsize=6)
ax2.set_xlim((xmin2-2, xmax2+2))
ax2.set_ylim((ymin2-ymax2*0.3, ymax2+ymax2*0.3))
ax2.set_title(label="Projected Load on Beam")

st.pyplot(fig)

dist_loads = []
inner = []
for idx, coord in enumerate(projected_poly_coords[1:-1]):
    if idx % 2 == 1:
        inner.append(coord)
        dist_loads.append(inner)
        inner = []
    else:
        inner.append(coord)

from PyNite import FEModel3D

# Create a new finite element model
simple_beam = FEModel3D()
simple_beam.add_material("default", E=1, G=1, nu=0.3, rho=1, fy=1)
simple_beam.add_load_combo("Projected", {"Case 1": 1.0})
simple_beam.add_load_combo("Smeared", {"Case 2": 1.0})

# Add nodes (14 ft = 168 in apart)
simple_beam.add_node('N1', 0, 0, 0)
simple_beam.add_node('N2', xmax2-xmin2, 0, 0)

# Add a beam with the following properties:
simple_beam.add_member('M1', 'N1', 'N2', 'default', Iy=1, Iz=1, J=1, A=1)

# Provide simple supports
simple_beam.def_support('N1', 1, 1, 1, 0, 0, 0)
simple_beam.def_support('N2', 1, 1, 1, 1, 0, 0)

# Add a uniform load of 200 lbs/ft to the beam
for dist_load in dist_loads:
    left, right = dist_load
    simple_beam.add_member_dist_load('M1', 'Fy', -left[1]/1000, -right[1]/1000, left[0], right[0],   case="Case 1")

# Provide simple supports
simple_beam.def_support('N1', 1, 1, 1, 0, 0, 0)
simple_beam.def_support('N2', 1, 1, 1, 1, 0, 0)

# Add a uniform load of 200 lbs/ft to the beam
for dist_load in dist_loads:
    left, right = dist_load
    simple_beam.add_member_dist_load('M1', 'Fy', -left[1]/1000, -right[1]/1000, left[0], right[0],   case="Case 1")

# Alternatively the following line would do apply the load to the full length of the member as well
load = total_load / (xmax2 - xmin2)
simple_beam.add_member_dist_load('M1', 'Fy', -load/1000, -load/1000, case="Case 2")

# Analyze the beam3
simple_beam.analyze()

projected_moment = simple_beam.Members['M1'].min_moment("Mz", "Projected")
smeared_moment = simple_beam.Members['M1'].min_moment("Mz", "Smeared")

st.write(f"Max Projected Moment: {round(projected_moment, 1)}")
st.write(f"Max Smeared Moment: {round(smeared_moment, 1)}")
msg = f":green[Smeared moment is conservative]" if abs(smeared_moment) > abs(projected_moment) else f":red[Smeared moment is NOT conservative]"
st.metric(label=msg, value=f"{round((smeared_moment - projected_moment)/projected_moment*100, 1)}%", )

st.sidebar.image("streamlit_app/logo-black.png")