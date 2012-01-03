import model

data = model.DataStore("test.sqlite")

for datum in ("{-100,-50,200,100}Foobar baz\n\nGrup grup jubyr fret yup.\nfkakeander f.",
              "{10,20,150,300}I'm a card with one line",
              "{200,200,150,100}No edges yet\n\nedges are too hard still. We'll do them later"):
      data.create_card(datum)

