class Add:
  """This is a test class."""

  def add(self, x: int, y: int) -> int:
    """Add two integers and return their sum

    :param x: first number to be added
    :type x: int
    :param y: second number to be added
    :type y: int
    
    :rtype int
    """

    return(x+y)

t = Add()
sum_ = t.add(37, 3)
print(sum_)