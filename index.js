let express = require('express');
let app = express();
let ejs = require('ejs');
//const haikus = require('./haikus.json');
const port = 6969;

app.set('view engine', 'ejs');
app.set('view cache', false);
app.use(express.static('/', {
  etag: false,
  lastModified: false,
  setHeaders: function (res, path) {
    res.setHeader('Cache-Control', 'no-store')
  }
}))
// Add the products/ folder to the static middleware
app.use('/products', express.static('products'));

const path = require('path');

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(port);
