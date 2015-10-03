from drunkenbishop.Atrium import Atrium
from drunkenbishop.Bishop import Bishop

class Fingerprint(object):

    def __init__(self, hash, key_type, hashtype):
        bishop = Bishop(76)
        self.atrium = Atrium(bishop, key_type, hashtype)
        moves = self.hash_to_moves(hash)
        lastmove = moves.pop()
        for move in moves:
            self.atrium.move(move)
        self.atrium.finalise(lastmove)


    def __str__(self):
        return str(self.atrium)

    def hash_to_moves(self, hash):
        moves =[]
        for word in hash:
            for pair in (3, 2, 1, 0):
                shift = pair*8
                byte = (word & (255 << shift)) >> shift
                for step in range(0, 8, 2):
                  mask = 3 << step
                  move = (byte & mask) >> step
                  moves.append(move)
        return moves