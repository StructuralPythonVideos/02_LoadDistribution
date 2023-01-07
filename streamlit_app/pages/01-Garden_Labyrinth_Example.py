import streamlit as st
import pathlib
from shapely import Polygon
from shapely.affinity import rotate, scale
from shapely.wkt import load as load_wkt
import polygon_generator as gen
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as PolygonPatch
from papermodels.models import load_distribution as ld

# From https://stackoverflow.com/questions/8997099/algorithm-to-generate-random-2d-polygon/25276331#25276331

here = pathlib.Path.cwd()#
st.write(here)

with open(here / 'labyrinth.wkt') as file:
    laby_poly = load_wkt(file)

scale_factor = st.sidebar.selectbox("Drawing Scale: 1 inch =", options=['1/8"', '1/4"', '1/2"'])
scale_factor = eval(scale_factor.replace('"', ''))
st.write(scale_factor)

total_load = st.sidebar.number_input("Set total soil weight", value=1000, step=10)

rotation_slider = st.sidebar.slider("Change rotation", min_value=0, max_value=90)
laby_poly = scale(laby_poly, xfact=scale_factor, yfact=scale_factor, origin="centroid")
laby_poly = rotate(laby_poly, angle=rotation_slider, use_radians=False)
xmin, ymin, xmax, ymax = laby_poly.bounds
laby_poly_coords = laby_poly.exterior.coords


projected_poly = ld.project_polygon(laby_poly, total_load=total_load)
projected_poly_xy = ld.project_polygon(laby_poly, total_load=total_load, xy=True)
projected_poly_coords = list(zip(*projected_poly_xy))
st.write(list(projected_poly.exterior.coords))
xmin2, ymin2, xmax2, ymax2 = projected_poly.bounds

fig, (ax, ax2) = plt.subplots(nrows=2, ncols=1, sharex=True)
poly_patch = PolygonPatch(laby_poly_coords)
ax.add_patch(poly_patch)


ax.set_xlim((xmin-2, xmax+2))
ax.set_ylim((ymin-2, ymax+2))
ax.set_title(label="Labyrinth shape in beam tributary area")

projected_poly_patch = PolygonPatch(projected_poly.exterior.coords, fc="#55aa99", ec="#666")
ax2.add_patch(projected_poly_patch)
for coord in projected_poly_coords:
    ax2.annotate(text=f"w={round(coord[1],1)};\nx={round(coord[0],1)}", xy=coord, fontsize=6)
ax2.set_xlim((xmin2-2, xmax2+2))
ax2.set_ylim((ymin2-ymax2*0.3, ymax2+ymax2*0.3))
ax2.set_title(label="Projected Load on Beam")


st.pyplot(fig)