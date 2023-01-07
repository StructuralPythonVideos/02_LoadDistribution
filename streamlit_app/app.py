import streamlit as st
from shapely import Polygon
import polygon_generator as gen
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as PolygonPatch
from papermodels.models import load_distribution as ld

# From https://stackoverflow.com/questions/8997099/algorithm-to-generate-random-2d-polygon/25276331#25276331

st.sidebar.write("## Random Polygon Generator")
irregularity_slider = st.sidebar.slider("Irregularity", min_value=0., max_value=1.0)
spikiness_slider = st.sidebar.slider("Spikiness", min_value=0., max_value=1.0)
num_vertices_slider = st.sidebar.slider("Number of vertices", min_value=4, max_value=30)
st.sidebar.write("---")
st.sidebar.write("## Apply load to polygon area")
total_load = st.sidebar.number_input(label="Total load of shape:", step=10)
st.sidebar.write("---")
test_poly_coords = gen.generate_polygon(#
    center=(0, 0),
    avg_radius=60,
    irregularity=irregularity_slider,
    spikiness=spikiness_slider,
    num_vertices=num_vertices_slider
)

test_poly = Polygon(test_poly_coords)
xmin, ymin, xmax, ymax = test_poly.bounds

projected_poly = ld.project_polygon(test_poly, total_load=total_load)
projected_poly_xy = ld.project_polygon(test_poly, total_load=total_load, xy=True)
projected_poly_coords = list(zip(*projected_poly_xy))
xmin2, ymin2, xmax2, ymax2 = projected_poly.bounds

fig, (ax, ax2) = plt.subplots(nrows=2, ncols=1, sharex=True)
poly_patch = PolygonPatch(test_poly_coords)
ax.add_patch(poly_patch)


ax.set_xlim((xmin-2, xmax+2))
ax.set_ylim((ymin-2, ymax+2))
ax.set_title(label="Randomly Generated Polygon Representing an Irregular Load in the Trib Area")

projected_poly_patch = PolygonPatch(projected_poly.exterior.coords, fc="#55aa99", ec="#666")
ax2.add_patch(projected_poly_patch)
for coord in projected_poly_coords:
    ax2.annotate(text=f"w={round(coord[1],1)};\nx={round(coord[0],1)}", xy=coord, fontsize=6)
ax2.set_xlim((xmin2-2, xmax2+2))
ax2.set_ylim((ymin2-ymax2*0.3, ymax2+ymax2*0.3))
ax2.set_title(label="Projected Load on Beam")


st.pyplot(fig)