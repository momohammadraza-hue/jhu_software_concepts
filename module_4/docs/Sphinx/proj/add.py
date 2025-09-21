class Add:
  """This is a test class."""

  def add(self, x: int, y: int) -> int:
      """Add two integers and return their sum

          :param x: add me first
          :type x: int
          :param y: add me second
          :type y: int

          :returns: summation of x and y

          :rtype: int

      """

      return (x + y)


t = Add()
sum_ = t.add(37, 3)
print(sum_)
