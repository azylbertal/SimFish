import numpy as np

import skimage.draw as draw
from skimage import io
import matplotlib.pyplot as plt

from Tools.ray_cast import rays


class DrawingBoard:

    def __init__(self, width, height):

        self.width = width
        self.height = height
        self.db = None
        self.erase()

    def get_area_mask(self):
        """Returns 2D area matrix UV-Red, A"""
        return self.db[:, :, :3]

    def erase(self, bkg=0):
        if bkg == 0:
            self.db = np.zeros((self.height, self.width, 3), dtype=np.double)
        else:
            self.db = np.ones((self.height, self.width, 3), dtype=np.double) * bkg

    def apply_light(self, dark_col, dark_gain, light_gain):
        self.db[:, :dark_col] *= dark_gain
        self.db[:, dark_col:] *= light_gain

    def circle(self, center, rad, color):
        rr, cc = draw.circle(center[1], center[0], rad, self.db.shape)
        self.db[rr, cc, :] = color

    def tail(self, head, left, right, tip, color):
        tail_coordinates = np.array((head, left, tip, right))
        rr, cc = draw.polygon(tail_coordinates[:, 1], tail_coordinates[:, 0], self.db.shape)
        self.db[rr, cc, :] = color

    def fish_shape(self, mouth_centre, mouth_rad, head_rad, tail_length, mouth_colour, body_colour, angle):
        offset = np.pi / 2
        angle += offset
        angle = -angle
        self.circle(mouth_centre, mouth_rad, mouth_colour)  # For the mouth.
        dx1, dy1 = head_rad * np.sin(angle), head_rad * np.cos(angle)
        head_centre = (mouth_centre[0] + dx1,
                       mouth_centre[1] + dy1)
        self.circle(head_centre, head_rad, body_colour)
        dx2, dy2 = -1 * dy1, dx1
        left_flank = (head_centre[0] + dx2,
                      head_centre[1] + dy2)
        right_flank = (head_centre[0] - dx2,
                       head_centre[1] - dy2)
        tip = (mouth_centre[0] + (tail_length + head_rad) * np.sin(angle),
               mouth_centre[1] + (tail_length + head_rad) * np.cos(angle))
        self.tail(head_centre, left_flank, right_flank, tip, body_colour)

    def create_screen(self, fish_position, distance, colour):
        rr, cc = draw.circle_perimeter(int(fish_position[0]), int(fish_position[1]), distance - 10)
        self.db[rr, cc, :] = colour
        rr, cc = draw.circle_perimeter(int(fish_position[0]), int(fish_position[1]), distance - 9)
        self.db[rr, cc, :] = colour
        rr, cc = draw.circle_perimeter(int(fish_position[0]), int(fish_position[1]), distance - 8)
        self.db[rr, cc, :] = colour

    def vegetation(self, vertex, edge_size, color):
        coordinates = np.array(((vertex[1], vertex[0]),
                                (vertex[1], vertex[0] + edge_size),
                                (vertex[1] + edge_size / 2, vertex[0] + edge_size - edge_size / 3),
                                (vertex[1] + edge_size, vertex[0] + edge_size),
                                (vertex[1] + edge_size, vertex[0]),
                                (vertex[1] + edge_size / 2, vertex[0] + edge_size / 3)))

        rr, cc = draw.polygon(coordinates[:, 0], coordinates[:, 1], self.db.shape)
        self.db[rr, cc, :] = color

    @staticmethod
    def multi_circles(cx, cy, rad):
        rr, cc = draw.circle(0, 0, rad)
        rrs = np.tile(rr, (len(cy), 1)) + np.tile(np.reshape(cy, (len(cy), 1)), (1, len(rr)))
        ccs = np.tile(cc, (len(cx), 1)) + np.tile(np.reshape(cx, (len(cx), 1)), (1, len(cc)))
        return rrs, ccs

    def line(self, p1, p2, color):
        rr, cc = draw.line(p1[1], p1[0], p2[1], p2[0])
        self.db[rr, cc, :] = color

    def get_size(self):
        return self.width, self.height

    def read(self, xmat, ymat):
        n_arms = xmat.shape[0]
        res = np.zeros((n_arms, 3))
        for arm in range(n_arms):
            [rr, cc] = draw.line(ymat[arm, 0].astype(int), xmat[arm, 0].astype(int), ymat[arm, 1].astype(int),
                                 xmat[arm, 1].astype(int))
            prfl = self.db[rr, cc]
            # prfl = np.array(profile_line(self.db, (ymat[arm,0], xmat[arm,0]), (ymat[arm,1], xmat[arm,1]), order=0, cval=1.))
            ps = np.sum(prfl, 1)
            if len(np.nonzero(ps)[0]) > 0:
                res[arm, :] = prfl[np.nonzero(ps)[0][0], :]
            else:
                res[arm, :] = [0, 0, 0]

        # xmat_ = np.where((xmat<0) | (xmat>=self.width), 0, xmat)
        # ymat_ = np.where((ymat<0) | (ymat>=self.height), 0, ymat)
        #
        # res = self.db[ymat_, xmat_, :]
        # res[np.where((xmat<0)|xmat>=self.width)|(ymat<0)|(ymat>=self.height), :] = [1, 0, 0]
        return res

    def show(self):
        io.imshow(self.db)
        io.show()


def apply_mask(board, mask=np.ones((1500, 1500))/2):
    # new_board = np.zeros(board.shape)
    # for channel in range(board.shape[-1]):
    #     new_board[:, :, channel] = np.multiply(board[:, :, channel], mask)
    # return new_board
    mask = np.expand_dims(mask, 2)
    return board * mask


def create_scatter_mask(position=(250, 250), decay_rate=0.0001):
    mask = np.fromfunction(lambda i, j: np.exp(-decay_rate * (((position[0]-i)**2 + (position[1]-j)**2) ** 0.5)), (1500, 1500), dtype=float)
    return mask


def show_mask(mask):
    extent = [0, 500, 0, 500]

    plt.clf()
    plt.imshow(mask, extent=extent, origin='lower')
    plt.show()


def show(board):
    # board = add_redundant_channel(board)
    io.imshow(board)
    io.show()


def add_redundant_channel(board):
    """Adds empty channel for initialisation purposes"""
    redundant_channel = np.zeros((board.shape[0], board.shape[1], 1))
    return np.concatenate((board, redundant_channel), axis=2)


def remove_green_channel(board):
    """Removes the green channel, which is not used."""
    board = np.delete(board, 1, 2)
    return board


if __name__ == "__main__":
    d = DrawingBoard(1500, 1500)
    d.circle((100, 200), 100, (1, 0, 0))
    d.line((50, 50), (100, 200), (0, 0, 1))
    d.show()
    x = d.get_area_mask()
    x = apply_mask(x)
    y = create_scatter_mask()
    show_mask(y)
    x = apply_mask(x, y)
    x = remove_green_channel(x)
    x = add_redundant_channel(x)
    show(x)







