import streamlit as st
import pathlib

st.write(
    """
    # Determine beam loading for complicated and non-convex shapes in beam tributary area

    When performing load checks on beams, sometimes loads are funny shapes or they are a regular shape but
    the load is being projected onto the beam at an angle.

    This application showcases a module from the free and open-source Python package `papermodels`, in development by StructuralPython. 
    The module calculates the shape of an irregularly shaped load within a beam's (or girder's) tributary area.
    In other words, it "projects" the polygon onto the beam and scales the resulting polygon so its total
    load adds up to a given total load provided by the user.

    Using this tool, a comparison is made, using a simply supported beam, of the total moment due to the projected
    load and compared to the total moment of a "smeared" uniform distributed load of the same magnitude over the same distance.
    It shows that, depending on the shape, using a smeared load can either be overly conservative (indicating savings
    are possible using the projected load) or that using a smeared load is not conservative.

    These examples are generally unitless. However, they were programmed using units of "inches" and "pounds" in mind.
    
    The module which can be found here:

    https://github.com/StructuralPython/papermodels/blob/main/src/papermodels/models/load_distribution.py
    """
)
here = pathlib.Path.cwd()
st.sidebar.image("logo-black.png")