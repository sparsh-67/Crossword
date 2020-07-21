import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        d={}
        for var in self.domains:
            d[var]=None
        return self.backtrack(d)

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for var in self.domains:
            for possible in list(self.domains[var]):
                if len(possible)!=var.length:
                    self.domains[var].remove(possible)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        raise NotImplementedError

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        for var in self.domains:
            for nbr in self.crossword.neighbors(var):
                cell=self.crossword.overlaps.get((var,nbr),None)
                if cell!=None:
                    for possible1 in list(self.domains[var]):
                        found_any=False
                        for possible2 in list(self.domains[nbr]):
                            if possible2[cell[1]]==possible1[cell[0]]:
                                found_any=True 
                                break
                        if not found_any:
                            self.domains[var].remove(possible1)
    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for var in assignment:
            if assignment[var]==None:
                return False

        return True 
    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        taken=set()
        for var in assignment:
            if assignment[var] in taken:
                return False
            taken.add(assignment[var])
            mynbrs=self.crossword.neighbors(var)
            for nbr in mynbrs:
                cell=self.crossword.overlaps.get((var,nbr),None)
                if cell!=None and assignment[var][cell[0]]!=assignment[nbr][cell[1]]:
                    return False

        return True 

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        ll=[]
        for val in self.domains[var]:
            ct=0
            for nbr in self.crossword.neighbors(var):
                if val in self.domains[nbr]:
                    ct+=1
            ll.append((ct,val))
        ll.sort()
        temp=[i[1] for i in ll]
        return temp


    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        def getdeg(var):
            ct=0
            for val in self.crossword.overlaps.keys():
                if var in val:
                    ct+=1 
            return ct
        myval=float('inf')
        mydeg=0
        myans=None
        for var in assignment:
            if assignment[var]!=None:
                continue
            if len(self.domains[var])<myval:
                myval=len(self.domains[var])
                mydeg=getdeg(var)
                myans=var
            elif len(self.domains[var])==myval and mydeg<getdeg(var):
                mydeg=getdeg(var)
                myans=var
        return myans 


    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment) and self.consistent(assignment):
            return assignment
        if self.assignment_complete(assignment):
            return None
        var=self.select_unassigned_variable(assignment)
        if assignment[var]==None:
            for possible in self.order_domain_values(var,assignment):
                if len(possible)==var.length:
                    assignment[var]=possible
                    removed={}
                    for nbr in self.crossword.neighbors(var):
                        cell=self.crossword.overlaps.get((var,nbr),None)
                        if cell!=None:
                            for val in list(self.domains[nbr]):
                                if val[cell[1]]!=possible[cell[0]]:
                                    if nbr not in removed:
                                        removed[nbr]=set()
                                    removed[nbr].add(val)
                                    self.domains[nbr].remove(val)


                    tryit=self.backtrack(assignment)
                    if tryit!=None:
                        return tryit
                    for nbr in removed:
                        self.domains[nbr]|=removed[nbr]
                    assignment[var]=None 
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
