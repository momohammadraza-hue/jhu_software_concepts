# module
class Docstring:
  """Module-level docstring"""

  # function
  def function_():
    """Function-level docstring"""
    pass

# print the docs associated with the module
print(Docstring.__doc__)

# print the docs associated with the function
print(Docstring.function_.__doc__)



