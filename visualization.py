import MDAnalysis
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import py3Dmol
import streamlit as st
import sys
sys.path.insert(1, 'ProbeParticleEllipsoid/')
from ellipse_lib import atom, ellipse

def write_pdb_with_pore_surface(path='', name='', end_radius=15, num_circle = 24):
    conf = path + name[:-4] + '.sph'
    top = conf
    sph = MDAnalysis.Universe(top, conf, topology_format='pdb', format='pdb') # tpr_resid_from_one=True
    radii = sph.atoms.occupancies
    resids = sph.atoms.resids
    sel = sph.select_atoms('resid '+str(min(resids[radii < end_radius ])) +':'+ str(max(resids[radii < end_radius ])) )
    n_residues = len(sel)
    n_atoms = num_circle * len(sel)
    ### create resindex list ###
    resindices = np.repeat(range(num_circle), len(sel))
    assert len(resindices) == n_atoms
    ### all water molecules belong to 1 segment ###
    segindices = [0] * n_residues
    ### create universe ###
    sol2 = MDAnalysis.Universe.empty(n_atoms,
                                n_residues=n_residues,
                                atom_resindex=resindices,
                                residue_segindex=segindices,
                                trajectory=True) # necessary for adding coordinates
    sol2.add_TopologyAttr('name', ['point']*n_residues*num_circle)
    sol2.add_TopologyAttr('resname', ['Pathway']*n_residues)
    sol2.add_TopologyAttr('resid', list(range(1, n_residues+1)))
    coordinates = []
    for count, atom in enumerate(sel):
        probe1 = sph.select_atoms('resname SPH and resid '+str(atom.resid))
        r = radii[np.where(resids==atom.resid)[0][0] ]
        for i in range(0,num_circle):
            p = probe1.positions[0] + r * np.array([np.cos(2*np.pi*i/num_circle), np.sin(2*np.pi*i/num_circle),0])
            coordinates.append(p)
    coord_array = np.array(coordinates)
    #assert coord_array.shape == (n_atoms, 1)
    sol2.atoms.positions = coord_array
    sel = sol2.select_atoms('name *')
    sel.write(path + name + '_circle.pdb')

def write_pdb_with_ellipsoid_surface(p, pdbname ,fname,  num_circle = 24):
    ### load ellipsoid output file ###
    df = pd.read_csv(p+fname, skiprows=1, header=0, 
                     names=['x', 'y', 'z', 'a', 'b', 'theta'])
    ### cooridnates of point cloud ###
    coordinates = []
    x = np.array(df['x'])
    y = np.array(df['y'])
    z = np.array(df['z'])
    larger = np.array(df['a'])
    smaller = np.array(df['b'])
    theta = np.array(df['theta'])
    n = len(x)
    dist_prev = 0
    large_dist_prev = 0
    max_smaller = max(smaller)

    ### write vmd surface ###
    f = open(p + pdbname+'_pathway_ellipse.vmd','w')
    f.write('color Display Background white\n')
    f.write('mol modstyle 0 top NewCartoon\n')
    f.write('mol modcolor 0 top ColorID 2\n') ###2 = grey ###
    f.write('draw delete all\n')
    f.write('draw materials off\n')
    f.write('draw color yellow\n')

    ### Loop for vmd and pdb file ###
    for i in range(n):
        # test for bulk:
        if i>0: 
            dist_prev = np.linalg.norm( np.array([x[i],y[i]]) -  np.array([x[i-1],y[i-1]]) )
        dist_prev = larger[i] / smaller[i] 
        #if (dist_prev > 1.75 or larger[i]>2*max_smaller) and (i<0.05*n or i>0.95*n):
        if larger[i]>50:
            print('ATTENTION at slice',i, 'with z=',z[i], 'dist_prev=',dist_prev,'larger', larger[i]  )
            large_dist_prev += 1
        else:
            e = ellipse(a=larger[i], b=smaller[i], theta=theta[i], cx=x[i], cy=y[i])
            x_vec, y_vec = e.draw(res = 2*np.pi/ num_circle )

            if smaller[i]<1.15:
                f.write('draw color red\n')
            elif smaller[i]>1.15 and smaller[i]<2.3:
                f.write('draw color green\n')
            else:
                f.write('draw color blue\n')

            for j in range(len(x_vec)):
                coordinates.append([x_vec[j], y_vec[j], z[i] ])
                string = 'draw point  { '+str(x_vec[j])+' '+str(y_vec[j])+' '+str(z[i]) + '}\n'
                f.write(string)
    f.close()        
    n_atoms = len(coordinates)  

    ### create universe for point cloud ###
    n_residues = len(x) - large_dist_prev
    ### create resindex list ###
    resindices = np.repeat(range(n_residues), len(x_vec))
    assert len(resindices) == n_atoms
    ### all water molecules belong to 1 segment ###
    segindices = [0] * n_residues
    sol2 = MDAnalysis.Universe.empty(n_atoms,
                                n_residues=n_residues,
                                atom_resindex=resindices,
                                residue_segindex=segindices,
                                trajectory=True) # necessary for adding coordinates
    sol2.add_TopologyAttr('name', ['point']*n_atoms)
    sol2.add_TopologyAttr('resname', ['Pathway']*n_residues)
    sol2.add_TopologyAttr('resid', list(range(1, n_residues+1)))
    ### write point cloud in pdb format ###
    sol2.atoms.positions = coordinates
    sel = sol2.select_atoms('name *')
    sel.write(p + pdbname + '_ellipsoid.pdb')



def plt_ellipsoid_pathway(df_res, f_size=22, title='', end_radius=15):
    z = df_res['z']
    a = df_res['a']
    b = df_res['b']
    #theta = df_res['theta']
    #print(min(z), max(z))
    fig, ax = plt.subplots()
    ax.set_ylim([0, end_radius + 5])
    plt.plot(z, a, label='Larger radius of ellipsoid')
    plt.plot(z, b, label='Smaller radius of ellipsoid\n=radius of spherical probe')
    plt.ylabel(r"Pathway radii ($\AA$)", fontsize=f_size)
    plt.xlabel(r"z-coordinate ($\AA$)", fontsize=f_size)
    title_str = 'Pathfinding with ellipsoidal probe'
    if title!='':
        title_str = title_str + '\n' + title
    plt.title(title_str, fontsize=f_size)

    ax.tick_params(axis='both', which='major', labelsize=f_size)
    ax.legend(prop={'size': 12}) # loc='upper center'
    fig.tight_layout()
    #fig.savefig('GlyR/asymmetric_channel_ellipse_pathway.png', bbox_inches='tight')  
    #plt.show()
    return fig

def pathway_visu(path, name, f_end='_circle.pdb'):
    with open(path+name) as ifile:
            system = "".join([x for x in ifile])
    xyzview = py3Dmol.view(height=800, width=800,) 
    xyzview.addModelsAsFrames(system)
    xyzview.setStyle({'model': -1}, {"cartoon": {'color': 'spectrum'}})
    with open(path+name + f_end) as ifile:
        sph2 = "".join([x for x in ifile])
    xyzview.addModelsAsFrames(sph2)
    xyzview.addSurface(py3Dmol.SES,{'opacity':0.9,'color':'lightblue'}, {'model': -1})
    xyzview.zoomTo()
    return xyzview

def st_write_ellipsoid():
    st.subheader("Path finding with ellipsoidal probe particle")
    string1 = '1. Load HOLE output file with positions and radii of probes.\n'
    string2 = '2. Loop through all spherical probe particles:\n'
    string3 = 'a) Ellipsoid initialized with spherical probe particle parameters from HOLE output.\n'
    string4 = 'b) First Nelder-Mead 4-dim optimization to insert ellipsoid with smaller bounds for parameters [x, y, r1, θ ].\n'
    string5 = 'c) Second optimization with larger boundaries for parameters to further increase ellipsoid.\n'
    string6 = 'The loop takes around 60s to complete...'
    st.write(string1+string2+string3+string4+string5+string6)

def example_xy_plane(f_size):
    a_vec = [atom(x=3.8,y=4.8,r=2), atom(-1,-3,r=2.7), atom(-4,4,r=1), atom(7,2,r=1), 
         atom(7.9,-1,r=1.5), atom(-3,1,r=1), atom(-0.0,4.8,r=1.3), atom(3,-2.9,r=1.0)
        ]
    probe = atom(2,1,r=2)
    p0 = ellipse(a=probe.r, b=probe.r, theta=0, cx=probe.x, cy=probe.y)

    p_example = ellipse(a=1.5*probe.r, b=probe.r, theta=0, cx=probe.x, cy=probe.y)

    p2 = ellipse(a=4.69050294820025, b=p0.b, theta=-0.33648560328658467, 
                cx=2.061766530062544, cy=1.061766530062543)

    f_size = 22

    t = np.arange(0, 2*np.pi, 0.01)
    fig, ax = plt.subplots()
    plt.title('Example of growing probe\nparticles in the xy-plane ', fontsize=f_size)

    ### probe ###
    x0, y0 = p0.draw()
    ax.plot(x0, y0, color='blue')
    ax.plot(probe.x,probe.y, '-x', color='blue')
    ### vdw particles ###
    for a in a_vec:
        vdw = ellipse(a=a.r, b=a.r, theta=0, cx=a.x, cy=a.y)
        x0, y0 = vdw.draw()
        ax.plot(x0, y0, color='black')
        ax.plot(a.x,a.y, '-x', color='black')
    ### ellipsoids ###
    x1, y1 = p_example.draw()
    ax.plot(x1, y1, color='green')
    ax.plot(p_example.cx, p_example.cy, '-x', color='green')

    x2, y2 = p2.draw()
    ax.plot(x2, y2, color='brown')
    ax.plot(p2.cx, p2.cy, '-x', color='brown')

    ax.set_xlabel("x", fontsize=f_size)
    ax.set_ylabel("y", fontsize=f_size)
    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.set_aspect('equal', adjustable='box')
    plt.gca().set_aspect('equal', adjustable='box')
    fig.tight_layout()
    return fig