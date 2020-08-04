"""
SF45.py

Description:
    SNL configuration class.

Created: June 18, 2020

"""
import numpy as np
import matplotlib
import pathlib
import inspect
import yaml as _yaml_
try:
    matplotlib.use("TkAgg")
except:
    pass
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from geometry import Point, Line, Patch, segment_intersect, angle_between, rotate, find_split_index


class SF45():
    def __init__(self, Ingrid_obj, config):

        self.parent = Ingrid_obj
        self.config = config
        self.settings = Ingrid_obj.settings
        self.plate_data = Ingrid_obj.plate_data

        self.parent.order_target_plates()
        self.PatchTagMap = self.parent.GetPatchTagMap(config='SF45')

        self.eq = Ingrid_obj.eq
        self.efit_psi = Ingrid_obj.efit_psi
        self.psi_norm = Ingrid_obj.psi_norm
        self.eq = Ingrid_obj.eq
        self.CurrentListPatch={}
        self.Verbose=False
        self.plate_data = Ingrid_obj.plate_data
        self.CorrectDistortion={}

    def patch_diagram(self):
        """ Generates the patch diagram for a given configuration. """

        colors = ['salmon', 'skyblue', 'mediumpurple', 'mediumaquamarine',
                  'sienna', 'orchid', 'lightblue', 'gold', 'steelblue',
                  'seagreen', 'firebrick', 'saddlebrown', 'c',
                  'm', 'dodgerblue', 'darkorchid', 'crimson',
                  'darkorange', 'lightgreen', 'lightseagreen', 'indigo',
                  'mediumvioletred', 'mistyrose', 'darkolivegreen', 'rebeccapurple']

        self.FigPatch=plt.figure('INGRID: Patch Map', figsize=(6, 10))
        self.FigPatch.clf()
        ax=self.FigPatch.subplots(1,1)
        plt.xlim(self.efit_psi.rmin, self.efit_psi.rmax)
        plt.ylim(self.efit_psi.zmin, self.efit_psi.zmax)
        ax.set_aspect('equal', adjustable='box')

        ax.set_xlabel('R')
        ax.set_ylabel('Z')
        self.FigPatch.suptitle('SNL Patch Diagram')

        for i, patch in enumerate(self.patches.values()):
            patch.plot_border('green')
            patch.fill(colors[i])
            patch.color=colors[i]
        ax.legend()
        plt.show()

    def grid_diagram(self,ax=None):
        """
        Create Grid matplotlib figure for an SNL object.
        @author: watkins35, garcia299
        """
        fig=plt.figure('INGRID: Grid', figsize=(6,10))
        if ax is None:
            ax=fig.gca()
        for patch in self.patches:
            patch.plot_subgrid(ax)
            print('patch completed...')

        plt.xlim(self.efit_psi.rmin, self.efit_psi.rmax)
        plt.ylim(self.efit_psi.zmin, self.efit_psi.zmax)
        plt.gca().set_aspect('equal', adjustable='box')
        plt.xlabel('R')
        plt.ylabel('Z')
        plt.title('INGRID SNL Subgrid')
        plt.show()

    def get_config(self):
        """
        Returns a string indicating whether the
        """
        return self.config

    def concat_grid(self):
        """
        Concatenate all local grids on individual patches into a single
        array with branch cuts
        Parameters:
        ----------
            config : str
                Type of SNL grid to concat.
        """
        patch_matrix = self.patch_matrix

        for patch in self.patches.values():
            patch.npol = len(patch.cell_grid[0]) + 1
            patch.nrad = len(patch.cell_grid) + 1

        # Total number of poloidal indices in all subgrids.
        np_total1 = int(np.sum([patch.npol - 1 for patch in patch_matrix[1][1:5]])) + 2

        # Total number of radial indices in all subgrids.
        nr_total1 = int(np.sum([patch[1].nrad - 1 for patch in patch_matrix[1:4]])) + 2

        # Total number of poloidal indices in all subgrids.
        np_total2 = int(np.sum([patch.npol - 1 for patch in patch_matrix[1][7:11]])) + 2

        # Total number of radial indices in all subgrids.
        nr_total2 = int(np.sum([patch[7].nrad - 1 for patch in patch_matrix[1:4]])) + 2

        rm1 = np.zeros((np_total1, nr_total1, 5), order = 'F')
        zm1  = np.zeros((np_total1, nr_total1, 5), order = 'F')
        rm2 = np.zeros((np_total2, nr_total2, 5), order = 'F')
        zm2  = np.zeros((np_total2, nr_total2, 5), order = 'F')

        ixcell = 0
        jycell = 0

        # Iterate over all the patches in our DNL configuration (we exclude guard cells denoted by '[None]')
        for ixp in range(1, 5):

            nr_sum = 0
            for jyp in range(1, 4):
                # Point to the current patch we are operating on.
                local_patch = patch_matrix[jyp][ixp]

                if local_patch == [None]:
                    continue

                nr_sum += local_patch.nrad - 1

                # Access the grid that is contained within this local_patch.
                # ixl - number of poloidal cells in the patch.
                for ixl in range(len(local_patch.cell_grid[0])):
                    # jyl - number of radial cells in the patch
                    for jyl in range(len(local_patch.cell_grid)):

                        ixcell = int(np.sum([patch.npol - 1 for patch in patch_matrix[1][1:ixp+1]])) \
                                - len(local_patch.cell_grid[0]) + ixl + 1

                        jycell = nr_sum - (local_patch.nrad - 1) + jyl + 1

                        ind = 0
                        for coor in ['CENTER', 'SW', 'SE', 'NW', 'NE']:
                            rm1[ixcell][jycell][ind] = local_patch.cell_grid[jyl][ixl].vertices[coor].x
                            zm1[ixcell][jycell][ind] = local_patch.cell_grid[jyl][ixl].vertices[coor].y
                            ind += 1
                            if Verbose: print('Populated RM/ZM entry ({}, {}) by accessing cell ({}, {}) from patch "{}"'.format(ixcell, jycell, jyl, ixl, local_patch.patchName))

        # Iterate over all the patches in our DNL configuration (we exclude guard cells denoted by '[None]')

        ixcell = 0
        jycell = 0

        for ixp in range(7, 11):

            nr_sum = 0
            for jyp in range(1, 4):
                # Point to the current patch we are operating on.
                local_patch = patch_matrix[jyp][ixp]

                if local_patch == [None]:
                    continue

                nr_sum += local_patch.nrad - 1

                # Access the grid that is contained within this local_patch.
                # ixl - number of poloidal cells in the patch.
                for ixl in range(len(local_patch.cell_grid[0])):
                    # jyl - number of radial cells in the patch
                    for jyl in range(len(local_patch.cell_grid)):

                        ixcell = int(np.sum([patch.npol - 1 for patch in patch_matrix[1][7:ixp+1]])) \
                                - len(local_patch.cell_grid[0]) + ixl + 1

                        jycell = nr_sum - (local_patch.nrad - 1) + jyl + 1

                        ind = 0
                        for coor in ['CENTER', 'SW', 'SE', 'NW', 'NE']:
                            rm2[ixcell][jycell][ind] = local_patch.cell_grid[jyl][ixl].vertices[coor].x
                            zm2[ixcell][jycell][ind] = local_patch.cell_grid[jyl][ixl].vertices[coor].y
                            ind += 1
                            if Verbose: print('Populated RM/ZM entry ({}, {}) by accessing cell ({}, {}) from patch "{}"'.format(ixcell, jycell, jyl, ixl, local_patch.patchName))

        # Flip indices into gridue format.
        for i in range(len(rm1)):
            rm1[i] = rm1[i][::-1]
        for i in range(len(zm1)):
            zm1[i] = zm1[i][::-1]
        for i in range(len(rm2)):
            rm2[i] = rm2[i][::-1]
        for i in range(len(zm2)):
            zm2[i] = zm2[i][::-1]

        # Add guard cells to the concatenated grid.
        ixrb1 = len(rm1) - 2
        ixlb1 = 0
        ixrb2 = len(rm2) - 2
        ixlb2 = 0

        rm1 = self.add_guardc(rm1, ixlb1, ixrb1)
        zm1 = self.add_guardc(zm1, ixlb1, ixrb1)
        rm2 = self.add_guardc(rm2, ixlb2, ixrb2)
        zm2 = self.add_guardc(zm2, ixlb2, ixrb2)

        self.rm = np.concatenate((rm1, rm2))
        self.zm = np.concatenate((zm1, zm2))

        try:
            debug = self.settings['DEBUG']['visual']['gridue']
        except:
            debug = False

        if debug:
            self.animate_grid()

    def construct_patches(self):
        """
        Draws lines and creates patches for both USN and LSN configurations.

        Patch Labeling Key:
            I: Inner,
            O: Outer,
            DL: Divertor Leg,
            PF: Private Flux,
            T: Top,
            B: Bottom,
            S: Scrape Off Layer,
            C: Core.
        """
        def reorder_limiter(new_start, limiter):
            start_index, = find_split_index(new_start, limiter)
            return limiter
        def limiter_split(start, end, limiter):
            start_index, sls = find_split_index(start, limiter)
            end_index, sls = find_split_index(end, limiter)
            if end_index <= start_index:
                limiter.p = limiter.p[start_index:] + limiter.p[:start_index]
            return limiter

        try:
            visual = self.settings['DEBUG']['visual']['patch_map']
        except KeyError:
            visual = False
        try:
            verbose = self.settings['DEBUG']['verbose']['patch_generation']
        except KeyError:
            verbose = False
        try:
            inner_tilt = self.settings['grid_params']['patch_generation']['inner_tilt']
        except KeyError:
            inner_tilt = 0.0
        try:
            outer_tilt = self.settings['grid_params']['patch_generation']['outer_tilt']
        except KeyError:
            outer_tilt = 0.0

        xpt1 = self.eq.NSEW_lookup['xpt1']['coor']
        xpt2 = self.eq.NSEW_lookup['xpt2']['coor']

        magx = np.array([self.settings['grid_params']['rmagx'] + self.settings['grid_params']['patch_generation']['rmagx_shift'], \
            self.settings['grid_params']['zmagx'] + self.settings['grid_params']['patch_generation']['zmagx_shift']])

        psi_max_west = self.settings['grid_params']['psi_max_west']
        psi_max_east = self.settings['grid_params']['psi_max_east']
        psi_min_core = self.settings['grid_params']['psi_min_core']
        psi_min_pf = self.settings['grid_params']['psi_min_pf']
        psi_min_pf_2 = self.settings['grid_params']['psi_pf2']

        if self.settings['limiter']['use_limiter']:
            WestPlate1 = self.parent.limiter_data.copy()
            WestPlate2 = self.parent.limiter_data.copy()

            EastPlate1 = self.parent.limiter_data.copy()
            EastPlate2 = self.parent.limiter_data.copy()

        else:
            WestPlate1 = Line([Point(i) for i in self.plate_W1])
            WestPlate2 = Line([Point(i) for i in self.plate_W2])

            EastPlate1 = Line([Point(i) for i in self.plate_E1])
            EastPlate2 = Line([Point(i) for i in self.plate_E2])

        # Generate Horizontal Mid-Plane lines
        LHS_Point = Point(magx[0] - 1e6 * np.cos(inner_tilt), magx[1] - 1e6 * np.sin(inner_tilt))
        RHS_Point = Point(magx[0] + 1e6 * np.cos(inner_tilt), magx[1] + 1e6 * np.sin(inner_tilt))
        west_midLine = Line([LHS_Point, RHS_Point])
        # inner_midLine.plot()

        LHS_Point = Point(magx[0] - 1e6 * np.cos(outer_tilt), magx[1] - 1e6 * np.sin(outer_tilt))
        RHS_Point = Point(magx[0] + 1e6 * np.cos(outer_tilt), magx[1] + 1e6 * np.sin(outer_tilt))
        east_midLine = Line([LHS_Point, RHS_Point])
        # outer_midLine.plot()

        # Generate Vertical Mid-Plane line
        Lower_Point = Point(magx[0], magx[1] - 1e6)
        Upper_Point = Point(magx[0], magx[1] + 1e6)
        topLine = Line([Lower_Point, Upper_Point])
        # topLine.plot()


        # Tracing primary-separatrix: core-boundary

        # H1_E / B1_W 
        xpt1N__psiMinCore = self.eq.draw_line(xpt1['N'], {'psi' : psi_min_core}, \
            option = 'rho', direction = 'cw', show_plot = visual, text = verbose)
        E1_E = xpt1N__psiMinCore
        B1_W = E1_E.reverse_copy()

        # B1_N / B2_S
        xpt1NW__west_midLine = self.eq.draw_line(xpt1['NW'], {'line' : west_midLine}, \
            option = 'theta', direction = 'cw', show_plot = visual, text = verbose)
        B1_N = xpt1NW__west_midLine
        B2_S = B1_N.reverse_copy()

        # H2_S / H1_N
        xpt1NE__east_midLine = self.eq.draw_line(xpt1['NE'], {'line' : east_midLine}, \
            option = 'theta', direction = 'ccw', show_plot = visual, text = verbose)
        E1_N = xpt1NE__east_midLine.reverse_copy()
        E2_S = E1_N.reverse_copy()

        # C1_N / C2_S
        west_midLine__topLine = self.eq.draw_line(xpt1NW__west_midLine.p[-1], {'line' : topLine}, \
            option = 'theta', direction = 'cw', show_plot = visual, text = verbose)
        C1_N = west_midLine__topLine
        C2_S = C1_N.reverse_copy()

        # D1_N / D2_S
        east_midLine__topLine = self.eq.draw_line(xpt1NE__east_midLine.p[-1], {'line' : topLine}, \
            option = 'theta', direction = 'ccw', show_plot = visual, text = verbose)
        D1_N = east_midLine__topLine.reverse_copy()
        D2_S = D1_N.reverse_copy()

        # Tracing core: psi-min-core region (rho = 1)
        
        # / B1_S
        psiMinCore__west_midLine_core = self.eq.draw_line(xpt1N__psiMinCore.p[-1], {'line' : west_midLine}, \
            option = 'theta', direction = 'cw', show_plot = visual, text = verbose)
        B1_S = psiMinCore__west_midLine_core.reverse_copy()

        # H1_E1
        psiMinCore__east_midLine_core = self.eq.draw_line(xpt1N__psiMinCore.p[-1], {'line' : east_midLine}, \
            option = 'theta', direction = 'ccw', show_plot = visual, text = verbose)
        E1_S = psiMinCore__east_midLine_core

        # / C1_S
        west_midLine_core__topLine = self.eq.draw_line(psiMinCore__west_midLine_core.p[-1], {'line' : topLine}, \
            option = 'theta', direction = 'cw', show_plot = visual, text = verbose)
        C1_S = west_midLine_core__topLine.reverse_copy()

        # D1_S
        east_midLine_core__topLine = self.eq.draw_line(psiMinCore__east_midLine_core.p[-1], {'line' : topLine}, \
            option = 'theta', direction = 'ccw', show_plot = visual, text = verbose)
        D1_S = east_midLine_core__topLine

        # A1_E / I1_W
        xpt1__psiMinPF1 = self.eq.draw_line(xpt1['S'], {'psi' : psi_min_pf}, \
            option = 'rho', direction = 'cw', show_plot = visual, text = verbose)
        A1_E = xpt1__psiMinPF1
        F1_W = A1_E.reverse_copy()

        # A1_S
        psiMinPF1__WestPlate1 = self.eq.draw_line(xpt1__psiMinPF1.p[-1], {'line' : WestPlate1}, \
            option = 'theta', direction = 'ccw', show_plot = visual, text = verbose)
        A1_S = psiMinPF1__WestPlate1

        # / I1_S
        psiMinPF1__EastPlate1 = self.eq.draw_line(xpt1__psiMinPF1.p[-1], {'line' : EastPlate1}, \
            option = 'theta', direction = 'cw', show_plot = visual, text = verbose)
        
        # !!! I1_S = psiMinPF1__EastPlate1.reverse_copy()

        # A2_S / A1_N
        xpt1__WestPlate1 = self.eq.draw_line(xpt1['SW'], {'line' : WestPlate1}, \
            option = 'theta', direction = 'ccw', show_plot = visual, text = verbose)
        A2_S = xpt1__WestPlate1
        A1_N = A2_S.reverse_copy()

        # I1_N / I2_S
        xpt1__EastPlate1 = self.eq.draw_line(xpt1['SE'], {'line' : EastPlate1}, \
            option = 'theta', direction = 'cw', show_plot = visual, text = verbose)

        # Drawing the portion of the separatrix found in the double-null configuration

        # E2_E / H2_W
        F2_E = self.eq.draw_line(xpt2['N'], {'line' : xpt1__EastPlate1}, \
            option = 'rho', direction = 'cw', show_plot = visual, text = verbose)
        F1_E = self.eq.draw_line(F2_E.p[-1], {'line' : psiMinPF1__EastPlate1}, \
            option = 'rho', direction = 'cw', show_plot = visual, text = verbose)

        I1_W = F1_E.reverse_copy()
        I2_W = F2_E.reverse_copy()

        F1_N, I1_N = xpt1__EastPlate1.split(I2_W.p[0], add_split_point=True)
        I2_S = I1_N.reverse_copy()
        F2_S = F1_N.reverse_copy()
        I1_S, F1_S = psiMinPF1__EastPlate1.reverse_copy().split(I1_W.p[0], add_split_point=True)
        
        # H2_N__I2_N
        I2_N = self.eq.draw_line(xpt2['NW'], {'line' : EastPlate1}, \
            option = 'theta', direction = 'cw', show_plot = visual, text = verbose)
        I3_S = I2_N.reverse_copy()

        # E3_S / E2_N
        xpt2NE__east_midLine = self.eq.draw_line(xpt2['NE'], {'line' : east_midLine}, \
            option = 'theta', direction = 'ccw', show_plot = visual, text = verbose)
        F2_W = self.eq.draw_line(xpt1['E'], {'line' : xpt2NE__east_midLine}, \
            option = 'rho', direction = 'ccw', show_plot = visual, text = verbose)
        E2_E = F2_W.reverse_copy()

        E2_N, F2_N = xpt2NE__east_midLine.reverse_copy().split(F2_W.p[-1], add_split_point=True)
        F3_S = F2_N.reverse_copy()
        E3_S = E2_N.reverse_copy()

        # D3_S / D2_N
        xpt2__east_midLine__topLine = self.eq.draw_line(xpt2NE__east_midLine.p[-1], {'line' : topLine}, 
            option = 'theta', direction = 'ccw', show_plot = visual, text = verbose)
        D3_S = xpt2__east_midLine__topLine
        D2_N = D3_S.reverse_copy()

        # C3_S / C2_N
        xpt2__topLine__west_midLine = self.eq.draw_line(xpt2__east_midLine__topLine.p[-1], {'line' : west_midLine},
            option = 'theta', direction = 'ccw', show_plot = visual, text = verbose)
        C3_S = xpt2__topLine__west_midLine
        C2_N = C3_S.reverse_copy()

        xpt2__west_midLine__WestPlate1 = self.eq.draw_line(xpt2__topLine__west_midLine.p[-1], {'line' : WestPlate1},
            option = 'theta', direction = 'ccw', show_plot = visual, text = verbose)


        B2_W = self.eq.draw_line(xpt1['W'], {'line' : xpt2__west_midLine__WestPlate1},
            option = 'rho', direction = 'ccw', show_plot = visual, text = verbose)
        A2_E = B2_W.reverse_copy()

        # / A3_S, B3_S
        A2_N, B2_N = xpt2__west_midLine__WestPlate1.reverse_copy().split(B2_W.p[-1], add_split_point=True)
        A3_S = A2_N.reverse_copy()
        B3_S = B2_N.reverse_copy()

        xpt2__psiMinPF2 = self.eq.draw_line(xpt2['S'], {'psi' : psi_min_pf_2}, \
            option = 'rho', direction = 'cw', show_plot = visual, text = verbose)

        G1_W, G2_W = xpt2__psiMinPF2.reverse_copy().split(xpt2__psiMinPF2.p[len(xpt2__psiMinPF2.p)//2], add_split_point = True)
        H1_E = G1_W.reverse_copy()
        H2_E = G2_W.reverse_copy()

        G1_S = self.eq.draw_line(G1_W.p[0], {'line' : EastPlate2}, option = 'theta', direction = 'cw',
            show_plot = visual, text = verbose).reverse_copy()
        H1_S = self.eq.draw_line(G1_W.p[0], {'line' : WestPlate2}, option = 'theta', direction = 'ccw',
            show_plot = visual, text = verbose)
        
        G1_N = self.eq.draw_line(G2_W.p[0], {'line' : EastPlate2}, option = 'theta', direction = 'cw',
            show_plot = visual, text = verbose)
        G2_S = G1_N.reverse_copy()

        H1_N = self.eq.draw_line(G2_W.p[0], {'line' : WestPlate2}, option = 'theta', direction = 'ccw',
            show_plot = visual, text = verbose).reverse_copy()
        H2_S = H1_N.reverse_copy()

        G2_N = self.eq.draw_line(xpt2['SE'], {'line' : EastPlate2}, option = 'theta', direction = 'cw',
            show_plot = visual, text = verbose)
        G3_S = G2_N.reverse_copy()

        H2_N = self.eq.draw_line(xpt2['SW'], {'line' : WestPlate2}, option = 'theta', direction = 'ccw',
            show_plot = visual, text = verbose).reverse_copy()
        H3_S = H2_N.reverse_copy()


        H3_E = self.eq.draw_line(xpt2['W'], {'psi' : psi_max_east}, option = 'rho', direction = 'ccw',
            show_plot = visual, text = verbose).reverse_copy()
        I3_W = H3_E.reverse_copy()


        H3_N = self.eq.draw_line(H3_E.p[0], {'line' : EastPlate1}, option = 'theta',
            direction = 'ccw', show_plot = visual, text = verbose).reverse_copy()

        I3_N = self.eq.draw_line(H3_E.p[0], {'line' : EastPlate1}, option = 'theta',
            direction = 'cw', show_plot = visual, text = verbose)

        G3_W = self.eq.draw_line(xpt2['E'], {'psi' : psi_max_west}, option = 'rho',
            direction = 'ccw', show_plot = visual, text = verbose)
        F3_E = G3_W.reverse_copy()


        G3_N = self.eq.draw_line(G3_W.p[-1], {'line' : EastPlate2}, option = 'theta', 
            direction = 'cw', show_plot = visual, text = verbose)

        G3_W__east_midLine = self.eq.draw_line(G3_W.p[-1], {'line' : east_midLine}, option = 'theta',
            direction = 'ccw', show_plot = visual, text = verbose)

        F3_W = self.eq.draw_line(F2_W.p[-1], {'line' : G3_W__east_midLine}, option = 'rho',
            direction = 'ccw', show_plot = visual, text = verbose)
        E3_E = F3_W.reverse_copy()
        
        E3_N, F3_N = G3_W__east_midLine.reverse_copy().split(F3_W.p[-1], add_split_point=True)

        D3_N = self.eq.draw_line(E3_N.p[0], {'line' : topLine}, option = 'theta', direction = 'ccw', 
            show_plot = visual, text = verbose).reverse_copy()
        C3_N = self.eq.draw_line(D3_N.p[0], {'line' : west_midLine}, option = 'theta', direction = 'ccw',
            show_plot = visual, text = verbose).reverse_copy()

        west_midLine__WestPlate1 = self.eq.draw_line(C3_N.p[0], {'line' : WestPlate1}, option = 'theta', direction = 'ccw',
            show_plot = visual, text = verbose)
        B3_W = self.eq.draw_line(B2_W.p[-1], {'line' : west_midLine__WestPlate1}, option = 'rho', direction = 'ccw',
            show_plot = visual, text = verbose)
        A3_E = B3_W.reverse_copy()

        A3_N, B3_N = west_midLine__WestPlate1.reverse_copy().split(B3_W.p[-1], add_split_point=True)

        B1_E = self.eq.draw_line(B1_N.p[-1], {'psi_horizontal' : psi_min_core}, option = 'z_const', 
            direction = 'cw', show_plot = visual, text = verbose)
        C1_W = B1_E.reverse_copy()

        B2_E = self.eq.draw_line(B2_N.p[-1], {'psi_horizontal' : 1.0}, option = 'z_const', 
            direction = 'cw', show_plot = visual, text = verbose)
        C2_W = B2_E.reverse_copy()

        B3_E = self.eq.draw_line(B3_N.p[-1], {'psi_horizontal' : Point(xpt2['center']).psi(self)}, option = 'z_const', 
            direction = 'cw', show_plot = visual, text = verbose)
        C3_W = B3_E.reverse_copy()

        C1_E = self.eq.draw_line(C1_N.p[-1], {'psi_vertical' : psi_min_core}, option = 'r_const', 
            direction = 'ccw', show_plot = visual, text = verbose)
        D1_W = C1_E.reverse_copy()

        C2_E = self.eq.draw_line(C2_N.p[-1], {'psi_vertical' : 1.0}, option = 'r_const', 
            direction = 'ccw', show_plot = visual, text = verbose)
        D2_W = C2_E.reverse_copy()

        C3_E = self.eq.draw_line(C3_N.p[-1], {'psi_vertical' : Point(xpt2['center']).psi(self)}, option = 'r_const', 
            direction = 'ccw', show_plot = visual, text = verbose)
        D3_W = C3_E.reverse_copy()

        E1_W = self.eq.draw_line(E1_N.p[0], {'psi_horizontal' : psi_min_core}, option = 'z_const', 
            direction = 'ccw', show_plot = visual, text = verbose).reverse_copy()
        D1_E = E1_W.reverse_copy()

        E2_W = self.eq.draw_line(E2_N.p[0], {'psi_horizontal' : 1.0}, option = 'z_const', 
            direction = 'ccw', show_plot = visual, text = verbose).reverse_copy()
        D2_E = E2_W.reverse_copy()

        E3_W = self.eq.draw_line(E3_N.p[0], {'psi_horizontal' : Point(xpt2['center']).psi(self)}, option = 'z_const', 
            direction = 'ccw', show_plot = visual, text = verbose).reverse_copy()
        D3_E = E3_W.reverse_copy()


        try:
            A1_W = (WestPlate1.split(A1_S.p[-1])[1]).split(A1_N.p[0], add_split_point = True)[0]
        except:
            A1_W = limiter_split(A1_S.p[-1], A1_N.p[0], WestPlate1).split(A1_S.p[-1])[1].split(A1_N.p[0], add_split_point = True)[0]
        try:
            A2_W = (WestPlate1.split(A2_S.p[-1])[1]).split(A2_N.p[0], add_split_point = True)[0]
        except:
            A2_W = limiter_split(A2_S.p[-1], A2_N.p[0], WestPlate1).split(A2_S.p[-1])[1].split(A2_N.p[0], add_split_point = True)[0]
        try:
            A3_W = (WestPlate1.split(A3_S.p[-1])[1]).split(A3_N.p[0], add_split_point = True)[0]
        except:
            A3_W = limiter_split(A3_S.p[-1], A3_N.p[0], WestPlate1).split(A3_S.p[-1])[1].split(A3_N.p[0], add_split_point = True)[0]

        try:
            H1_W = (WestPlate2.split(H1_S.p[-1])[1]).split(H1_N.p[0], add_split_point = True)[0]
        except:
            H1_W = limiter_split(H1_S.p[-1], H1_N.p[0], WestPlate2).split(H1_S.p[-1])[1].split(H1_N.p[0], add_split_point = True)[0]
        try:
            H2_W = (WestPlate2.split(H2_S.p[-1])[1]).split(H2_N.p[0], add_split_point = True)[0]
        except:
            H2_W = limiter_split(H2_S.p[-1], H2_N.p[0], WestPlate2).split(H2_S.p[-1])[1].split(H2_N.p[0], add_split_point = True)[0]
        try:
            H3_W = (WestPlate2.split(H3_S.p[-1])[1]).split(H3_N.p[0], add_split_point = True)[0]
        except:
            H3_W = limiter_split(H3_S.p[-1], H3_N.p[0], WestPlate2).split(H3_S.p[-1])[1].split(H3_N.p[0], add_split_point = True)[0]

        try:
            I1_E = (EastPlate1.split(I1_N.p[-1])[1]).split(I1_S.p[0], add_split_point = True)[0]
        except:
            I1_E = limiter_split(I1_N.p[-1], I1_S.p[0], EastPlate1).split(I1_N.p[-1])[1].split(I1_S.p[0], add_split_point = True)[0]
        try:
            I2_E = (EastPlate1.split(I2_N.p[-1])[1]).split(I2_S.p[0], add_split_point = True)[0]
        except:
            I2_E = limiter_split(I2_N.p[-1], I2_S.p[0], EastPlate1).split(I2_N.p[-1])[1].split(I2_S.p[0], add_split_point = True)[0]
        try:
            I3_E = (EastPlate1.split(I3_N.p[-1])[1]).split(I3_S.p[0], add_split_point = True)[0]
        except:
            I3_E = limiter_split(I3_N.p[-1], I3_S.p[0], EastPlate1).split(I3_N.p[-1])[1].split(I3_S.p[0], add_split_point = True)[0]
        try:
            G1_E = (EastPlate2.split(G1_N.p[-1])[1]).split(G1_S.p[0], add_split_point = True)[0]
        except:
            G1_E = limiter_split(G1_N.p[-1], G1_S.p[0], EastPlate2).split(G1_N.p[-1])[1].split(G1_S.p[0], add_split_point = True)[0]
        try:
            G2_E = (EastPlate2.split(G2_N.p[-1])[1]).split(G2_S.p[0], add_split_point = True)[0]
        except:
            G2_E = limiter_split(G2_N.p[-1], G2_S.p[0], EastPlate2).split(G2_N.p[-1])[1].split(G2_S.p[0], add_split_point = True)[0]
        try:
            G3_E = (EastPlate2.split(G3_N.p[-1])[1]).split(G3_S.p[0], add_split_point = True)[0]
        except:
            G3_E = limiter_split(G3_N.p[-1], G3_S.p[0], EastPlate2).split(G3_N.p[-1])[1].split(G3_S.p[0], add_split_point = True)[0]

        # ============== Patch A1 ==============
        location = 'W'
        A1 = Patch([A1_N, A1_E, A1_S, A1_W], patchName = 'A1', platePatch = True, plateLocation = location)
        # ============== Patch A2 ==============
        location = 'W'
        A2 = Patch([A2_N, A2_E, A2_S, A2_W], patchName = 'A2', platePatch = True, plateLocation = location)
        # ============== Patch A3 ==============
        location = 'W'
        A3 = Patch([A3_N, A3_E, A3_S, A3_W], patchName = 'A3', platePatch = True, plateLocation = location)


        # ============== Patch B1 ==============
        B1 = Patch([B1_N, B1_E, B1_S, B1_W], patchName = 'B1')
        # ============== Patch B2 ==============
        B2 = Patch([B2_N, B2_E, B2_S, B2_W], patchName = 'B2')
        # ============== Patch B3 ==============
        B3 = Patch([B3_N, B3_E, B3_S, B3_W], patchName = 'B3')

        # ============== Patch C1 ==============
        C1 = Patch([C1_N, C1_E, C1_S, C1_W], patchName = 'C1')
        # ============== Patch C2 ==============
        C2 = Patch([C2_N, C2_E, C2_S, C2_W], patchName = 'C2')
        # ============== Patch C3 ==============
        C3 = Patch([C3_N, C3_E, C3_S, C3_W], patchName = 'C3')

        # ============== Patch D1 ==============
        D1 = Patch([D1_N, D1_E, D1_S, D1_W], patchName = 'D1')
        # ============== Patch D2 ==============
        D2 = Patch([D2_N, D2_E, D2_S, D2_W], patchName = 'D2')
        # ============== Patch D3 ==============
        D3 = Patch([D3_N, D3_E, D3_S, D3_W], patchName = 'D3')

        # ============== Patch E1 ==============
        E1 = Patch([E1_N, E1_E, E1_S, E1_W], patchName = 'E1')
        # ============== Patch E2 ==============
        E2 = Patch([E2_N, E2_E, E2_S, E2_W], patchName = 'E2')
        # ============== Patch E3 ==============
        E3 = Patch([E3_N, E3_E, E3_S, E3_W], patchName = 'E3')

        # ============== Patch F1 ==============
        F1 = Patch([F1_N, F1_E, F1_S, F1_W], patchName = 'F1')
        # ============== Patch F2 ==============
        F2 = Patch([F2_N, F2_E, F2_S, F2_W], patchName = 'F2')
        # ============== Patch F3 ==============
        F3 = Patch([F3_N, F3_E, F3_S, F3_W], patchName = 'F3')

        # ============== Patch G1 ==============
        G1 = Patch([G1_N, G1_E, G1_S, G1_W], patchName = 'G1')
        # ============== Patch G2 ==============
        G2 = Patch([G2_N, G2_E, G2_S, G2_W], patchName = 'G2')
        # ============== Patch G3 ==============
        G3 = Patch([G3_N, G3_E, G3_S, G3_W], patchName = 'G3')

        # ============== Patch H1 ==============
        H1 = Patch([H1_N, H1_E, H1_S, H1_W], patchName = 'H1')
        # ============== Patch H2 ==============
        H2 = Patch([H2_N, H2_E, H2_S, H2_W], patchName = 'H2')
        # ============== Patch H3 ==============
        H3 = Patch([H3_N, H3_E, H3_S, H3_W], patchName = 'H3')

        # ============== Patch I1 ==============
        I1 = Patch([I1_N, I1_E, I1_S, I1_W], patchName = 'I1')
        # ============== Patch I2 ==============
        I2 = Patch([I2_N, I2_E, I2_S, I2_W], patchName = 'I2')
        # ============== Patch I3 ==============
        I3 = Patch([I3_N, I3_E, I3_S, I3_W], patchName = 'I3')

        patches = [A3, A2, A1, B3, B2, B1, C3, C2, C1, D3, D2, D1, E3, E2, E1,
                   F3, F2, F1, G3, G2, G1, H3, H2, H1, I3, I2, I1]

        self.patches = {}
        for patch in patches:
            patch.parent = self
            patch.PatchTagMap = self.PatchTagMap
            self.patches[patch.patchName] = patch


    def patch_diagram(self):
        """
        Generates the patch diagram for a given configuration.
        @author: watkins35, garcia299
        """

        colors = ['salmon', 'skyblue', 'mediumpurple', 'mediumaquamarine',
                  'sienna', 'orchid', 'lightblue', 'gold', 'steelblue',
                  'seagreen', 'firebrick', 'saddlebrown', 'dodgerblue',
                  'violet', 'magenta', 'olivedrab', 'darkorange', 'mediumslateblue',
                  'palevioletred', 'yellow', 'lightpink', 'plum', 'lawngreen',
                  'tan', 'hotpink', 'lightgray', 'darkcyan', 'navy']


        self.FigPatch=plt.figure('INGRID: Patch Map', figsize=(6, 10))
        self.FigPatch.clf()
        ax=self.FigPatch.subplots(1,1)
        plt.xlim(self.efit_psi.rmin, self.efit_psi.rmax)
        plt.ylim(self.efit_psi.zmin, self.efit_psi.zmax)
        ax.set_aspect('equal', adjustable='box')

        ax.set_xlabel('R')
        ax.set_ylabel('Z')
        self.FigPatch.suptitle('DNL Patch Diagram: ' + self.config)

        for i, patch in enumerate(self.patches.values()):
            patch.plot_border('green')
            patch.fill(colors[i])
            patch.color=colors[i]
        plt.show()

    def CheckPatches(self,verbose=False):
        for name, patch in self.patches.items():
            if patch.platePatch:
                print(' # Checking patch: ', name)
                patch.CheckPatch(self)


    def SetPatchBoundaryPoints(self,Patch):
        if self.ConnexionMap.get(Patch.get_tag()) is not None:
            if self.Verbose: print('Find connexion map for patch {}'.format(Patch.patchName))
            for Boundary,AdjacentPatch in self.ConnexionMap.get(Patch.get_tag()).items():
                Patch.BoundaryPoints[Boundary]=self.GetBoundaryPoints(AdjacentPatch)
                if self.Verbose: print('Find Boundaries points for {}'.format(Patch.patchName))

    def GetBoundaryPoints(self,AdjacentPatch):
        if AdjacentPatch is not None:
            PatchName=AdjacentPatch[0]
            Boundary=AdjacentPatch[1]
            for name, patch in self.patches.items():
                if name == PatchName:
                   if Boundary=='S':
                       return patch.S_vertices
                   elif Boundary=='N':
                       return patch.N_vertices
                   elif Boundary=='E':
                       return patch.W_vertices
                   elif Boundary=='W':
                       return patch.W_vertices 
        return None

    def GetNpoints(self,Patch,Enforce=True,Verbose=False):
        try:
            np_sol = self.settings['grid_params']['grid_generation']['np_sol']
        except:
            np_sol = self.settings['grid_params']['grid_generation']['np_global']
        try:
            np_core = self.settings['grid_params']['grid_generation']['np_core']
        except:
            np_core = self.settings['grid_params']['grid_generation']['np_global']
        try:
            np_pf = self.settings['grid_params']['grid_generation']['np_pf']
        except:
            np_pf = self.settings['grid_params']['grid_generation']['np_global']

        if np_sol != np_core:
            if Enforce:
                raise ValueError('SOL and CORE must have equal POLOIDAL np values')
            else:
                print('WARNING: SOL and CORE must have equal POLOIDAL np values!\nSetting np values' \
                + ' to the minimum of np_sol={} and np_core={}.\n'.format(np_sol,np_core))
            np_sol = np_core = np.amin([np_sol, np_core])

        try:
            nr_sol = self.settings['grid_params']['grid_generation']['nr_sol']
        except:
            nr_sol = self.settings['grid_params']['grid_generation']['nr_global']

        try:
            nr_core = self.settings['grid_params']['grid_generation']['nr_core']
        except:
            nr_core = self.settings['grid_params']['grid_generation']['nr_global']
        try:
            nr_pf = self.settings['grid_params']['grid_generation']['nr_pf']
        except:
            nr_pf = self.settings['grid_params']['grid_generation']['nr_global']

        if nr_pf != nr_core:
            if Enforce:
                raise ValueError('PF and CORE must have equal RADIAL nr values')
            else:
                print('WARNING: PF and CORE must have equal RADIAL nr values!\nSetting nr values' \
                + ' to the minimum of nr_pf={} and nr_core={}.\n'.format(nr_pf,nr_core))
                nr_pf = nr_core = np.amin([nr_pf, nr_core])

        if Patch.platePatch:
            if Patch.plateLocation == 'W':
                np_cells = self.settings['target_plates']['plate_W1']['np_local']
            elif Patch.plateLocation == 'E':
                np_cells = self.settings['target_plates']['plate_E1']['np_local']

        return (nr_cells,np_cells)

    def AdjustPatch(self,patch):
        xpt1 = Point(self.eq.NSEW_lookup['xpt1']['coor']['center'])
        xpt2 = Point(self.eq.NSEW_lookup['xpt2']['coor']['center'])

        tag = patch.get_tag()
        if tag == 'A2':
            patch.adjust_corner(xpt1, 'SE')
        elif tag == 'A1':
            patch.adjust_corner(xpt1, 'NE')
        elif tag == 'B2':
            patch.adjust_corner(xpt1, 'SW')
        elif tag == 'B1':
            patch.adjust_corner(xpt1, 'NW')
        elif tag == 'E2':
            patch.adjust_corner(xpt1, 'SE')
        elif tag == 'E1':
            patch.adjust_corner(xpt1, 'NE')
        elif tag == 'F3':
            patch.adjust_corner(xpt2, 'SE')
        elif tag == 'F2':
            patch.adjust_corner(xpt1, 'SW')
            patch.adjust_corner(xpt2, 'NE')
        elif tag == 'F1':
            patch.adjust_corner(xpt1, 'NW')
        elif tag == 'G3':
            patch.adjust_corner(xpt2, 'SW')
        elif tag == 'G2':
            patch.adjust_corner(xpt2, 'NW')
        elif tag == 'H3':
            patch.adjust_corner(xpt2, 'SE')
        elif tag == 'H2':
            patch.adjust_corner(xpt2, 'NE')


    def construct_grid(self, np_cells = 1, nr_cells = 1,Verbose=False,ShowVertices=False,RestartScratch=False,OptionTrace='theta',ExtraSettings={},ListPatches='all', Enforce=True):

        # Straighten up East and West segments of our patches,
        # Plot borders and fill patches.
        if Verbose: print('Construct Grid')
        try:
            visual = self.settings['DEBUG']['visual']['subgrid']
        except:
            visual = False
        try:
            verbose = self.settings['DEBUG']['verbose']['grid_generation']
        except:
            verbose = False

        verbose=Verbose or verbose
        
            
        print('>>> Patches:', [k for k in self.patches.keys()])
        if RestartScratch:
            self.CurrentListPatch={}
    
        for name, patch in self.patches.items():
            
            if self.CorrectDistortion.get(name) is not None:
               patch.CorrectDistortion=self.CorrectDistortion.get(name)
            elif self.CorrectDistortion.get('all') is not None:
                patch.CorrectDistortion=self.CorrectDistortion.get('all')
            else:
                patch.CorrectDistortion={'Active':False}
            if (ListPatches=='all' and patch not in self.CurrentListPatch) or (ListPatches!='all' and name in ListPatches):
                self.SetPatchBoundaryPoints(patch)
                (nr_cells,np_cells)=self.settings['grid_params']['grid_generation']['nr_global'], self.settings['grid_params']['grid_generation']['np_global']#self.GetNpoints(patch, Enforce=Enforce)
                (_radial_f,_poloidal_f)= lambda x: x, lambda x: x # self.GetFunctions(patch,ExtraSettings=ExtraSettings,Enforce=Enforce)
                print('>>> Making subgrid in patch:{} with np={},nr={},fp={},fr={}'.format(name, np_cells, nr_cells, inspect.getsource(_poloidal_f), inspect.getsource(_radial_f)))
                patch.make_subgrid(self, np_cells, nr_cells, _poloidal_f=_poloidal_f,_radial_f=_radial_f,verbose = verbose, visual = visual,ShowVertices=ShowVertices,OptionTrace=OptionTrace)
                self.AdjustPatch(patch)
                patch.plot_subgrid()
                self.CurrentListPatch[name] = patch
