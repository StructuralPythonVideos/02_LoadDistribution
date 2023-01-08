import streamlit as st
import pathlib
from shapely.affinity import rotate
from shapely.wkt import load as load_wkt
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as PolygonPatch
from papermodels.models import load_distribution as ld

# From https://stackoverflow.com/questions/8997099/algorithm-to-generate-random-2d-polygon/25276331#25276331

here = pathlib.Path.cwd()#

with open(here / 'planter.wkt') as file:#
    laby_poly = load_wkt(file)

total_load = st.sidebar.number_input("Set total soil weight", value=5000, step=10)

rotation_slider = st.sidebar.slider("Change rotation", min_value=0, max_value=90)
laby_poly = rotate(laby_poly, angle=rotation_slider, use_radians=False, origin='centroid')
xmin, ymin, xmax, ymax = laby_poly.bounds
laby_poly_coords = laby_poly.exterior.coords


projected_poly = ld.project_polygon(laby_poly, total_load=total_load)
projected_poly_xy = ld.project_polygon(laby_poly, total_load=total_load, xy=True)
projected_poly_coords = list(zip(*projected_poly_xy))
xmin2, ymin2, xmax2, ymax2 = projected_poly.bounds

fig, (ax, ax2) = plt.subplots(nrows=2, ncols=1, sharex=True)
poly_patch = PolygonPatch(laby_poly_coords)
ax.add_patch(poly_patch)


ax.set_xlim((xmin-10, xmax+10))
ax.set_ylim((ymin-2, ymax+2))
ax.set_title(label="Planter shape contained in beam tributary area")

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
# ax2.set_xlim((xmin2-xmin2*0.2, xmax2+xmax2*0.2))
ax2.set_ylim((ymin2-ymax2*0.3, ymax2+ymax2*0.3))
ax2.set_title(label="Projected Load on Beam")


st.pyplot(fig)

udls = []
inner = []
for idx, coord in enumerate(projected_poly_coords[1:-1]):
    if idx % 2 == 1:
        inner.append(coord)
        udls.append(inner)
        inner = []
    else:
        inner.append(coord)

from PyNite import FEModel3D

# Create a new finite element model
SimpleBeam = FEModel3D()
SimpleBeam.add_load_combo("Projected", {"Case 1": 1.0}, combo_type='strength')
SimpleBeam.add_load_combo("Smeared", {"Case 2": 1.0}, combo_type='strength')

# Add nodes (14 ft = 168 in apart)
SimpleBeam.add_node('N1', 0, 0, 0)
SimpleBeam.add_node('N2', xmax2-xmin2, 0, 0)

# Add a beam with the following properties:
# E = 29000 ksi, G = 11400 ksi, Iy = 100 in^4, Iz = 150 in^4, J = 250 in^4, A = 20 in^2
SimpleBeam.add_member('M1', 'N1', 'N2', 29000, 11400, 100, 150, 250, 20)

# Provide simple supports
SimpleBeam.def_support('N1', 1, 1, 1, 0, 0, 0)
SimpleBeam.def_support('N2', 1, 1, 1, 1, 0, 0)

# Add a uniform load of 200 lbs/ft to the beam
for udl in udls:
    left, right = udl
    SimpleBeam.add_member_dist_load('M1', 'Fy', -left[1]/1000, -right[1]/1000, left[0], right[0],   case="Case 1")

# Alternatively the following line would do apply the load to the full length of the member as well
load = total_load / (xmax2 - xmin2)
SimpleBeam.add_member_dist_load('M1', 'Fy', -load/1000, -load/1000, case="Case 2")

# Analyze the beam3
SimpleBeam.analyze()

projected_moment = SimpleBeam.Members['M1'].min_moment("Mz", "Projected")
smeared_moment = SimpleBeam.Members['M1'].min_moment("Mz", "Smeared")

st.write(f"Max Projected Moment: {round(projected_moment, 1)}")
st.write(f"Max Smeared Moment: {round(smeared_moment, 1)}")
msg = f":green[Smeared moment is conservative]" if abs(smeared_moment) > abs(projected_moment) else f":red[Smeared moment is NOT conservative]"
st.metric(label=msg, value=f"{round((smeared_moment - projected_moment)/projected_moment*100, 1)}%", )

st.sidebar.image("logo-black.png")