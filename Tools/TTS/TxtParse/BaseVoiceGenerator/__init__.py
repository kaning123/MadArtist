from . import Generators
#print(globals())

def GetGenerator(name):
    return getattr(Generators, name, None)

if __name__ == "__main__":
    print(GetGenerator("edge_tts_based_engine"))