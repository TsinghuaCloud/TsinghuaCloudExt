import MySQLdb
import MySQLdb.cursors

	
class DBConn:
	conn = None
	
	def connect(self):
		self.conn= MySQLdb.connect(	
			host='166.111.143.220',
			port = 3306,
			user='root',
			passwd='cloud',
			db ='glance',
			cursorclass = MySQLdb.cursors.DictCursor 
			)
	def cursor(self):
		try:
			return self.conn.cursor()
		except (AttributeError, MySQLdb.OperationalError):
			self.connect()
			return self.conn.cursor()
	def commit(self):
		return self.conn.commit()	
	def close(self):
		return self.conn.close()

