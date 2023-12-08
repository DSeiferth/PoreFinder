Usage
=====

.. _installation:

Installation
------------

To use PoreFinding, first install it using pip:

.. code-block:: console

   (.venv) $ pip install PoreFinding

Creating Pore profiles
----------------

To analyse ion channel pores, you can initialise ``PoreFinding.PoreAnalysis()`` class
with an array of pdb structures that you want to analyse.


For example:

>>> import PoreFinding as pf
>>> p = 'PoreFinding/pdb_models/'
>>> pdb_array = [p+'8fe1.pdb']
>>> c = pf.PoreAnalysis(pdb_array, num_circle=20,)
>>> c.hole_analysis(plot_lines=True, legend_outside=False, title='', f_size=15, )
>>> c.hole_df 
>>> c.pathway_visualisation(index_model=0, f_end='_circle.pdb')
>>> c.ellipsoid_analysis(index_model=0)
>>> c.pathway_visualisation(0, f_end='_ellipsoid.pdb')