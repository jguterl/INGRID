#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 25 16:00:04 2019

@author: watkins35
"""
from __future__ import print_function, division
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve, curve_fit, root_scalar


class Vector:
    """
    Defines a vector from a nontrivial origin.
    
    Parameters
    ----------
    xy : array-like
        Location of the vector. It if of the form (x, y).
    origin : array-like
        Location of the origin. This is to adjust for not being at the
        origin of the axes. Of the form (x, y).
    """
    def __init__(self, xy, origin):
        self.x, self.y = xy
        self.xorigin = origin[0]
        self.yorigin = origin[1]
        self.xnorm = self.x - self.xorigin
        self.ynorm = self.y - self.yorigin
        self.quadrant = (int(np.sign(self.xnorm)), int(np.sign(self.ynorm)))

    def arr(self):
        """ 
        Returns
        -------
        ndarray
            Returns the vector as an array.
        """
        return np.array([self.xnorm, self.ynorm])

    def mag(self):
        """  
        Returns
        -------
        float
            Computes the magnitude, or length of the vector.
        """
        return np.linalg.norm(self.arr())


class Point:
    """
    Point object 
    
    Parameters
    ----------
    pts : array-like
        Accepts either two values x, y as floats, or 
        a single tuple/list value (x, y).
    """
    
    def __init__(self, *pts):
        if np.shape(pts) == (2,):
            self.x, self.y = pts
        elif np.shape(pts) == (1, 2):
            self.x, self.y = pts[0]
        else:
            print('incompatible form')
            print(np.shape(pts), pts)

    def psi(self, grid, tag='v'):
        """ 
        Parameters
        ----------
        grid : Setup_Grid_Data.Efit_Data
            Must pass in the grid upon which the value of psi is to be
            calculated on. Must be the Efit grid object.
        tag : str, optional
            This is to specify the type of psi derivative, if desired. 
            Accepts 'v', 'vr', 'vz', 'vrz'.
            The default is 'v', or no derivative.
         
        Returns
        -------
        float
            Calculate the value of psi at the point.
        """
        return grid.psi_norm.get_psi(self.x, self.y, tag)

    def plot(self):
        """ Places an x on the location of the point. """
        plt.plot(self.x, self.y, 'x')


class Line:
    """ 
    Line object, in which an ordered set of points defines a line.
    
    Parameters
    ----------
    points : list
        Points are of the form p = (x, y), and the list should be
        made up of multiple points. [p, p, p]...  
    """

    def __init__(self, points):
        self.p = points
        self.xval = [p.x for p in points]
        self.yval = [p.y for p in points]
        self.length = self.calc_length()

            
    def reverse(self):    
        """ Points the line in the other direction.
        It is intended to be used right after generating a line  
        using the draw_line funciton from the line tracer. 
        For example; LineTracing.draw_line(args...).reverse().
        
        Returns
        -------
        self
            geometry.Line
        """
        self.p = self.p[::-1]
        return self

    def reverse_copy(self):
        """
        Returns a copy of the line in the reversed direction.
        Does not overwrite the current line.
        """

        return Line(self.p[::-1])

    def straighten(self):
        """
        Returns a Line instance consisting of the caller's
        first point and final point. To be used with 'curves'
        in order to generate chords.
        """

        return Line([self.p[0], self.p[-1]])

    def plot(self, color='#1f77b4'):
        """ Plots the line of the current figure.
        
        Parameters
        ----------
        color : str, optional
            Defaults to a light blue.
        """
        plt.plot(self.xval, self.yval, color=color, linewidth='1.5', zorder = 5)

    def print_points(self):
        """ Prints each point in the line to the terminal. """
        print([(p.x, p.y) for p in self.p])

    def divisions(self, num):
        """
        Splits the line into discrete segments.
        
        Parameters
        ----------
        num : int
            Number of points in the segmented line.
        """
        self.xs = np.linspace(self.p[0].x, self.p[-1].x, num)
        self.ys = np.linspace(self.p[0].y, self.p[-1].y, num)

    def fluff(self, num = 1000):
        x_fluff = np.empty(0)
        y_fluff = np.empty(0)
        for i in range(len(self.xval) - 1):
            x_fluff = np.append(x_fluff, np.linspace(self.xval[i], self.xval[i+1], num, endpoint = False))
            y_fluff = np.append(y_fluff, np.linspace(self.yval[i], self.yval[i+1], num, endpoint = False))
        x_fluff = np.append(x_fluff, self.xval[-1])
        y_fluff = np.append(y_fluff, self.yval[-1])

        return x_fluff, y_fluff
        
    def points(self):
        """ Returns the points in the line as a tuple. """
        return ((self.p[0].x, self.p[0].y), (self.p[-1].x, self.p[-1].y))

    def calc_length(self):
        l = 0
        for i in range(len(self.p) - 1):
            l += np.sqrt( (self.p[i+1].x - self.p[i].x) ** 2 + (self.p[i+1].y - self.p[i].y) ** 2)
        return l


class Cell:
    """
    Each Cell is contained within a patch

    Parameters:
    -----------
    vertices : geometry.Point
        Each cell is defined by four points in a clockwise order.
        NW -> NE -> SE -> SW
    """
    def __init__(self, lines):
        self.lines = lines
        self.N = lines[0]
        self.S = lines[1]
        self.E = lines[2]
        self.W = lines[3]

    def plot_border(self, color = 'blue'):
        for line in self.lines:
            line.plot()

class Patch:
    """
    Each patch contains a grid, and has it's own shape.
    
    Parameters
    ----------
    lines : geometry.Line
        Each patch defined by four lines in order - 
        Nline, Eline, Sline, Wline - order points to go clockwise.

    """
    
    def __init__(self, lines):
        self.lines = lines
        self.N = lines[0]
        self.E = lines[1]
        self.S = lines[2]
        self.W = lines[3]
        
        # This is the border for the fill function
        # It need to only include N and S lines
        self.p = list(self.N.p) + list(self.S.p)
        

    def plot_border(self, color='red'):
        """
        Draw solid borders around the patch.
        
        Parameters
        ----------
        color : str, optional
            Defaults to red.
        """
        for line in self.lines:
            line.plot(color)

    def fill(self, color='lightsalmon'):
        """
        Shades in the patch with a given color
        
        Parameters
        ----------
        color : str, optional
            Defaults to a light salmon.
        """
        x = [p.x for p in self.p]
        y = [p.y for p in self.p]
        plt.fill(x, y, facecolor=color)

    def plot_subgrid(self):
        for cell in self.cells:
            cell.plot_border()

    def make_subgrid(self, grid, num = 4):
        """
        Generate a refined grid within a patch.
        This 'refined-grid' within a Patch is a collection
        of num x num Cell objects

        Parameters:
        ----------
        grid : Ingrid object
                To be used for obtaining Efit data and all
                other class information.
        num  : int, optional
                Number to be used to generate num x num 
                cells within our Patch.
        """
        from scipy.interpolate import splprep, splev
        from scipy.optimize import root_scalar

        def psi_parameterize(grid, r, z):
            """
            Helper function to be used to generate a 
            list of values to parameterize a spline 
            in Psi. Returns a list to be used for splprep only
            """
            vmax = grid.psi_norm.get_psi(r[-1], z[-1])
            vmin = grid.psi_norm.get_psi(r[0], z[0])

            vparameterization = np.empty(0)
            for i in range(len(r)):
                vcurr = grid.psi_norm.get_psi(r[i], z[i])
                vparameterization = np.append(vparameterization, abs((vcurr - vmin) / (vmax - vmin)))

            return vparameterization

        # Allocate space for collection of cell objects.
        # Arbitrary 2D container for now.
        cell_list = []
        num += 1
        # Parameters to be used in generation of B-Splines.
        eps = 1e-5
        unew = np.arange(0, 1 + eps, eps)

        # Create B-Splines along the North and South boundaries.
        N_vals = self.N.fluff()

        N_spl, uN = splprep([N_vals[0], N_vals[1]], s = 0)
        # Reverse the orientation of the South line to line up with the North.

        S_vals = self.S.reverse_copy().fluff()
        S_spl, uS = splprep([S_vals[0], S_vals[1]], s = 0)


        # Create B-Splines along the East and West boundaries.
        # Parameterize EW splines in Psi
        # TODO: Currently linear along E and W. Generalize to curves...
        # rpts, zpts = np.linspace(self.W.p[0].x, self.W.p[-1].x, 1000), \
        #              np.linspace(self.W.p[0].y, self.W.p[-1].y, 1000)

        W_vals = self.W.fluff()
        W_spl, uW = splprep([W_vals[0], W_vals[1]], u = psi_parameterize(grid, W_vals[0], W_vals[1]), s = 0)
        
        # rpts, zpts = np.linspace(self.E.reverse_copy().p[0].x, self.E.reverse_copy().p[-1].x, 1000), \
        #              np.linspace(self.E.reverse_copy().p[0].y, self.E.reverse_copy().p[-1].y, 1000)

        E_vals = self.E.reverse_copy().fluff()
        E_spl, uE = splprep([E_vals[0], E_vals[1]], u = psi_parameterize(grid, E_vals[0], E_vals[1]), s = 0)      

        spl_data = {'N' : N_spl, 'S' : S_spl, 'E' : E_spl, 'W' : W_spl}
        N_spline = splev(uN, N_spl)
        S_spline = splev(uS, S_spl)
        E_spline = splev(uE, E_spl)
        W_spline = splev(uW, W_spl)

        # Generate our sub-grid anchor points along the North
        # and South boundaries of our patch.
        N_vertices = []
        S_vertices = []
        E_vertices = []
        W_vertices = []

        for i in range(num):
            _n = splev(i / (num-1), spl_data['N'])
            N_vertices.append(Point((_n[0], _n[1])))

            _s = splev(i / (num-1), spl_data['S'])
            S_vertices.append(Point((_s[0], _s[1])))

            _e = splev(i / (num-1), spl_data['E'])
            E_vertices.append(Point((_e[0], _e[1])))

            _w = splev(i / (num-1), spl_data['W'])
            W_vertices.append(Point((_w[0], _w[1])))

        for item in [N_vertices, S_vertices, E_vertices, W_vertices]:
            for vertex in item:
                plt.plot(vertex.x, vertex.y, '.', color = 'black')

        bounds = []
        colors = ['red', 'orange', 'green', 'blue', 'black']
        for i in range(num):
            upper = Point((N_vertices[i].x, N_vertices[i].y))
            lower = Point((S_vertices[i].x, S_vertices[i].y))
            bounds.append(Line([upper, lower]))

        def make_cell(SW_vert, NW_vert, endLine):
            print('Plotting N')
            N = grid.eq.draw_line(NW_vert, {'line' : endLine}, option = 'theta', direction = 'cw', show_plot = True)
            print('Plotting S')
            S = grid.eq.draw_line(SW_vert, {'line' : endLine}, option = 'theta', direction = 'cw', show_plot = True).reverse_copy()
            print('Plotting E')
            E = Line([N.p[-1], S.p[0]])
            print('Plotting W')
            W = Line([S.p[-1], N.p[0]])
            return Cell([N, S, E, W])
        
        # Prepare data to generate Cells.
        w_list = [p for p in W_vertices]
        bounds.pop(0)
        
        next_w = []
        for endLine in bounds:
            print(len(w_list))
            
            for i in range(len(w_list) - 1):
                new_cell = make_cell(w_list[i], w_list[i+1], endLine)
                new_cell.plot_border()
                next_w.append(new_cell.S.p[0])
                next_w.append(new_cell.N.p[-1])
                Line([next_w[i], next_w[i+1]]).plot(color = colors[i])
                cell_list.append(new_cell)
            w_list = list(dict.fromkeys([p for p in next_w]))
            next_w = []

        self.cells = cell_list
        """
        for i in range(len(W_vertices) - 1):
            grid.eq.draw_line(W_vertices[i + 1], {'line': self.E}, option = 'theta', direction = 'cw', show_plot = True).plot()

        for line in bounds:
            line.plot()
        """
        


    def make_subgrid2(self, grid, num = 4):
        """
        Generate a refined grid within a patch.
        This 'refined-grid' within a Patch is a collection
        of num x num Cell objects

        Parameters:
        ----------
        grid : Ingrid object
                To be used for obtaining Efit data and all
                other class information.
        num  : int, optional
                Number to be used to generate num x num 
                cells within our Patch.
        """
        from scipy.interpolate import splprep, splev
        from scipy.optimize import root_scalar

        def psi_parameterize(grid, r, z):
            """
            Helper function to be used to generate a 
            list of values to parameterize a spline 
            in Psi. Returns a list to be used for splprep only
            """
            vmax = grid.psi_norm.get_psi(r[-1], z[-1])
            vmin = grid.psi_norm.get_psi(r[0], z[0])

            vparameterization = np.zeros(len(unew))
            for i in range(len(unew)):
                vcurr = grid.psi_norm.get_psi(r[i], z[i])
                vparameterization[i] = abs((vcurr - vmin) / (vmax - vmin))

            return vparameterization

        # Allocate space for collection of cell objects.
        # Arbitrary 2D container for now.
        cell_list = []

        # Parameters to be used in generation of B-Splines.
        eps = 1e-5
        unew = np.arange(0, 1 + eps, eps)

        # Create B-Splines along the North and South boundaries.
        N_spl, uN = splprep([self.N.xval, self.N.yval], s = 0, t = len(self.N.xval))
        # Reverse the orientation of the South line to line up with the North.
        S_spl, uS = splprep([self.S.reverse_copy().xval, self.S.reverse_copy().yval], s = 0, t = len(self.S.xval))


        # Create B-Splines along the East and West boundaries.
        # Parameterize EW splines in Psi
        # TODO: Currently linear along E and W. Generalize to curves...
        rpts, zpts = np.linspace(self.W.p[0].x, self.W.p[-1].x, len(unew)), \
                     np.linspace(self.W.p[0].y, self.W.p[-1].y, len(unew))

        W_spl, uW = splprep([rpts, zpts], u = psi_parameterize(grid, rpts, zpts), s = 0)
        
        rpts, zpts = np.linspace(self.E.reverse_copy().p[0].x, self.E.reverse_copy().p[-1].x, len(unew)), \
                     np.linspace(self.E.reverse_copy().p[0].y, self.E.reverse_copy().p[-1].y, len(unew))

        E_spl, uE = splprep([rpts, zpts], u = psi_parameterize(grid, rpts, zpts), s = 0)      

        spl_data = {'N' : N_spl, 'S' : S_spl, 'E' : E_spl, 'W' : W_spl}
        N_spline = splev(uN, N_spl)
        S_spline = splev(uS, S_spl)
        E_spline = splev(uE, E_spl)
        W_spline = splev(uW, W_spl)

        # Generate our sub-grid anchor points along the North
        # and South boundaries of our patch.
        N_vertices = []
        S_vertices = []
        E_vertices = []
        W_vertices = []

        for i in range(num):
            _n = splev(i / (num-1), spl_data['N'])
            N_vertices.append(Point((_n[0], _n[1])))

            _s = splev(i / (num-1), spl_data['S'])
            S_vertices.append(Point((_s[0], _s[1])))

            _e = splev(i / (num-1), spl_data['E'])
            E_vertices.append(Point((_e[0], _e[1])))

            _w = splev(i / (num-1), spl_data['W'])
            W_vertices.append(Point((_w[0], _w[1])))

        for item in [N_vertices, S_vertices, E_vertices, W_vertices]:
            for vertex in item:
                plt.plot(vertex.x, vertex.y, '.', color = 'black')

        bounds = []
        for i in range(num):
            upper = Point((N_vertices[i].x, N_vertices[i].y))
            lower = Point((S_vertices[i].x, S_vertices[i].y))
            bounds.append(Line([upper, lower]))

        def make_cell(NW_vert, SW_vert, endLine):
            N = grid.eq.draw_line(NW_vert, {'line' : endLine}, option = 'theta', direction = 'cw', show_plot = True)       
            S = grid.eq.draw_line(SW_vert, {'line' : endLine}, option = 'theta', direction = 'cw', show_plot = True).reverse_copy()
            E = Line([N.p[-1], S.p[0]])
            W = Line([S.p[-1], N.p[0]])
            return Cell([N, S, E, W])

        NW_start = N_vertices[0]
        SW_start = S_vertices[0]

        r_line = [p for p in W_vertices]
        r_line.reverse()
        r_line.pop(0)

        for i in range(len(bounds)):
            NW_start = N_vertices[i]
            next_r = []
            while r_line:
                SW_start = r_line[0]
                r_line.pop(0)
                new_cell = make_cell(NW_start, SW_start, bounds[i + 1])
                NW_start = new_cell.S.p[-1]
                cell_list.append(new_cell)
                next_r.append(new_cell.N.p[-1])
            r_line = next_r
            r_line.pop(0)


        self.cells = cell_list


        """
        for i in range(num):
            for j in range(num):
                self.cells[i][j] = make_cell(grid, spl_dat, i, j)
 
        nline_pts = []
        sline_pts = []
        colors = ['red', 'blue', 'green', 'purple', 'magenta']


        for line in [nline, sline]:
            spl_dat, u = splprep([line.xval, line.yval], s = 0)  
            unew = np.arange(0, 1 + 1e-5, 1e-5)           
            _spline = splev(unew, spl_dat)
            plt.plot(_spline[0], _spline[1], color='blue', linewidth='2', zorder = 1)
        
            for i in range(num):
                _root = splev(i/(num-1), spl_dat)
                plt.plot(_root[0], _root[1], '.', color = colors[i], zorder = 2)
                if line is nline:
                    nline_pts.append(Point(_root))
                elif line is sline:
                    sline_pts.append(Point(_root))

        for i in range(num):
            grid_line = Line([nline_pts[i], sline_pts[num - i - 1]])
            grid_line.plot(color = colors[i])

        line = self.E
        rpts = np.linspace(line.p[-1].x, line.p[0].x, 100)
        zpts = np.linspace(line.p[-1].y, line.p[0].y, 100)

        psivals = np.zeros(len(rpts))

        psiStart = grid.psi_norm.get_psi(rpts[0], zpts[0])
        psiEnd = grid.psi_norm.get_psi(rpts[-1], zpts[-1])

        for i in range(len(psivals)):
            psiCurrent = grid.psi_norm.get_psi(rpts[i], zpts[i])
            psivals[i] = abs((psiCurrent - psiStart)/(psiEnd - psiStart))

        spl_dat, u = splprep([rpts, zpts], u = psivals, s = 0)
        unew = np.arange(0, 1 + 1e-7, 1e-7)           
        _spline = splev(unew, spl_dat)
        
        plt.plot(_spline[0], _spline[1], color='blue', linewidth='2', zorder = 1)
        
        for i in range(num):
            _root = splev(i/(num-1), spl_dat)
            plt.plot(_root[0], _root[1], '.', color = colors[i], zorder=2)
        """


        """
        for i in range(num):
            alpha = i / (num -1)

            psiN = self.N.p[0].psi(grid)
            psiS = self.S.p[-1].psi(grid)
            psiStart = psiN + alpha * (psiS - psiN)

            x1 = self.S.p[-1].x
            x2 = self.N.p[0].x
            y1 = self.S.p[-1].y
            y2 = self.N.p[0].y
            
            plt.plot(x2, y2, 'X', color='blue')  # north
            plt.plot(x1, y1, 'X', color='red')  # south
            plt.draw()
                    
            def fpsi(x):
                # line in 3d space
                # must manually calculate y each time we stick it into
                # the line of interest
                y = (y2-y1)/(x2-x1)*(x-x1)+y1
                return grid.psi_norm.get_psi(x, y) - psiStart

            sol = root_scalar(fpsi, bracket=[x1, x2])
            r_psi = sol.root
            z_psi = (y2-y1)/(x2-x1)*(r_psi-x1)+y1
            
            plt.plot(r_psi, z_psi, 'x')
            plt.draw()
            
            mid_line = grid.eq.draw_line((r_psi, z_psi), {'line': self.E},option='theta', direction='cw', show_plot=False)
        """

        """
        nr_subgrid = num
        np_subgrid = num

        psi_upper = grid.get_psi(self.N.p.x[0], self.N.p.y[0])
        psi_lower = grid.get_psi(self.S.p.x[-1], self.S.p.y[-1])

        psi_increments = np.linspace(psi_lower, psi_upper, num)
        """

        """
        def dL(s):
            dR = splev(s, spl_dat, der = 1)[0]
            dZ = splev(s, spl_dat, der = 1)[1]
            return np.sqrt( dR ** 2 + dZ ** 2)

        _spline_len = quad(dL, 0, 1)[0]
        """


        
    def refine(self, grid):
        """ Divides a patch into smaller cells based on N and S lines,
        and the psi levels of E and W lines.
        
        Parameters
        ----------
        grid : Setup_Grid_Data.Efit_Data
            Requires the grid the patches were calculated on.
        """
        
        # TODO: need a more universal fit for the function
        def f(x, a, b, c, d):
            # fit to a cubic polynomial
            return a + b*x + c*x**2 + d*x**3
        
        # curve fit return optimal Parameters and 
        # the covariance of those parameters
        poptN, pcovN = curve_fit(f, self.N.xval, self.N.yval)
        poptS, pcovS = curve_fit(f, self.S.xval, self.S.yval)
        
        x1 = np.linspace(self.N.xval[0], self.N.xval[-1])
        x2 = np.linspace(self.S.xval[0], self.S.xval[-1])
        
        plt.plot(x1, f(x1, *poptN), color='green')
        plt.plot(x2, f(x2, *poptS), color='magenta')
        plt.draw()
        
        
        # split horizontally 
        psiN = self.N.p[0].psi(grid)
        psiS = self.S.p[-1].psi(grid)
        
        alp = .5 # test split at half psi
        
        psiAlp = psiS + alp*(psiN - psiS)
                
        # TODO in the Ingrid.construct_SNL_patches method there must be some
        # inconsistency in the definition of lines, on the order isn't being 
        # maintained, because the below definition for the west endpoints
        # of the north and south lines is correct for most of the patches
        # but a few has one point on the wrong end.
        # these are: IDL, IST, OCB, and OPF
        x1 = self.S.p[-1].x
        x2 = self.N.p[0].x
        y1 = self.S.p[-1].y
        y2 = self.N.p[0].y
        
        plt.plot(x2, y2, 'X', color='blue')  # north
        plt.plot(x1, y1, 'X', color='red')  # south
        plt.draw()
                
        def fpsi(x):
            # line in 3d space
            # must manually calculate y each time we stick it into
            # the line of interest
            y = (y2-y1)/(x2-x1)*(x-x1)+y1
            return grid.psi_norm.get_psi(x, y) - psiAlp

        sol = root_scalar(fpsi, bracket=[x1, x2])
        r_psi = sol.root
        z_psi = (y2-y1)/(x2-x1)*(r_psi-x1)+y1
        
        plt.plot(r_psi, z_psi, 'x')
        plt.draw()
        
        mid_line = grid.eq.draw_line((r_psi, z_psi), {'line': self.E},option='theta', direction='cw', show_plot=True)
        
        self.lines.append(mid_line)
 

def calc_mid_point(v1, v2):
    """
    Calculates the bisection of two vectors of equal length, 
    and returns the point on the circle at that angle.
    
    
    Parameters
    ----------
    v1 : geometry.Vector
        v1 must be furthest right in a counter clockwise direction.
    v2 : geometry.Vector
        Vector on the left.
        
    Returns
    -------
    tuple
        The point at the bisection of two vectors.
    
    """
    # bisection
    theta = np.arccos(np.dot(v1.arr(), v2.arr())/(v1.mag() * v2.mag())) / 2.

    # check with quadrant the vectors are in and
    # compute the angles appropriately
    if v1.quadrant == (1, 1):
        # NE quadrant
        angle = np.arccos(v1.xnorm/v1.mag())
    elif v1.quadrant == (-1, 1):
        # NW quadrant
        angle = np.pi - np.arcsin(v1.ynorm/v1.mag())
    elif v1.quadrant == (-1, -1):
        # SW quadrant
        angle = np.pi + np.arctan(v1.ynorm/v1.xnorm)
    elif v1.quadrant == (1, -1):
        # SE quadrant
        angle = - np.arccos(v1.xnorm/v1.mag())
    else:
        print("Something went wrong")

    x = v1.xorigin + v1.mag() * np.cos(theta+angle)
    y = v1.yorigin + v1.mag() * np.sin(theta+angle)
    return x, y


def test2points(p1, p2, line):
    """
    Check if two points are on opposite sides of a given line.
        
    Parameters
    ----------
    p1 : tuple
        First point, (x, y)
    p2 : tuple
        Second point, (x, y)
    line : array-like
        The line is comprised of two points ((x, y), (x, y)).

    Returns
    -------
    tuple
        Returns two numbers, if the signs are different 
        the points are on opposite sides of the line.
    
    """    
    (x1, y1), (x2, y2) = line
    x, y = p1
    a, b = p2
    d1 = (x-x1)*(y2-y1)-(y-y1)*(x2-x1)
    d2 = (a-x1)*(y2-y1)-(b-y1)*(x2-x1)
    
    return np.sign(d1),  np.sign(d2)


def intersect(line1, line2):
    """ Finds the intersection of two line segments
    
    
    Parameters
    ----------
    line1 : array-like
    line2 : array-like
        Both lines of the form A = ((x, y), (x, y)).
        
    Returns
    -------
    tuple
        Coordinates of the intersection.
    
    """ 
    # TODO: Imporove this method so it can handle verticle lines.
    # there is a division by zero error in some DIII-D data caused by this.
    def line(x, line):
        """ Point slope form. """
        (x1, y1), (x2, y2) = line
        if x2-x1 == 0:
            x1 += 1e-4
        
        return (y2-y1)/(x2-x1) * (x - x1) + y1

    def f(xy):
        # parse the line, access any point
        # normalized to help solve for zero
        x, y = xy
        return np.array([y - line(x, line1),
                         y - line(x, line2)])

    # use the mean for initial guess
    (a, b), (c, d) = line1
    (i, j), (p, q) = line2
    guess = (np.mean([a, c, i, p]), np.mean([b, d, j, q]))
    r, z = fsolve(f, guess)
    return r, z

def segment_intersect(line1, line2):
    """ Finds the intersection of two FINITE line segments.

    Parameters
    ----------
    line1 : array-like
    line2 : array-like
        Both lines of the form line1 = (P1, P2), line2 = (P3, P4)

    Returns
    -------
    bool, tuple
        True/False of whether the segments intersect
        Coordinates of the intersection
    """

    (xa, ya), (xb, yb) = (line1.xval[0], line1.yval[0]), (line2.xval[0], line2.yval[0])
    (xc, yc), (xd, yd) = (line1.xval[1], line1.yval[1]), (line2.xval[1], line2.yval[1])


    print(xb - xa)
    print(yb - ya)
    M = np.array([[xb - xa, -xd + xc],\
                 [yb - ya, -yd + yc]])

    print(M)
    r = np.array([xc-xa, yc - ya])

    print(r)

    sol = np.linalg.solve(M, r)

    if sol[0] <= 1 and sol[1] <= 1\
       and sol[0] >= 0 and sol[1] >= 0:
           return True, sol
    else:
        False, (None,None)


if __name__ == "__main__":
    p1 = Point(1, 2)
    p2 = Point(3, 2)
    p3 = Point(4, 3)
    p4 = Point(2, 5)

    # functionality of a patch
    fig = plt.figure('patches', figsize=(6, 10))
    plt.clf()
    # pass in list of points - typically four
    patch = Patch([p1, p2, p3, p4])
    # plot the boundary

#    patch.plot_bounds()
    patch.fill('lightsalmon')

    # borders
    patch.plot_border('red')

    plt.xlim(0, 6)
    plt.ylim(0, 6)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.xlabel('R')
    plt.ylabel('Z')
    plt.title('Example Patch')
    plt.show()
