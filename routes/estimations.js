// routes/estimations.js
router.post('/', async (req, res) => {
  try {
    const estimation = new Estimation(req.body);
    await estimation.save();
    res.status(201).json(estimation);
  } catch (error) {
    res.status(400).json({ message: error.message });
  }
});

router.get('/:id', async (req, res) => {
  try {
    const estimation = await Estimation.findById(req.params.id)
      .populate('items.material');
    res.json(estimation);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});
