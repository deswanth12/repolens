const { queryDb } = require('./db');

function startServer() {
  const data = queryDb();
  console.log("Started server with data", data);
}

module.exports = { startServer };
