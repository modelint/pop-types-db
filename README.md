# Platform Independent Type Definition System

To support the specification of Shlaer-Mellor Executable UML models we need a way to define types (data types) that can be supported by a wide variety of platforms.

The [Shlaer-Mellor metamodel](https://github.com/modelint/shlaer-mellor-metamodel)  supports the use of types and operations on types in its action semantics, but it makes no attempt to define them.

This establishes a domain separation from Shlaer-Mellor semantics and type definition.

After all, a type definition system should not be incorporating any Shlaer-Mellor semantics, or in fact ANY modeling semantics.

A type definition system could have many uses that have nothing to do with modeling.
