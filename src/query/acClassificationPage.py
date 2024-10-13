
queryStr = """
{
result: acClassificationPage {
  	id
}
}

"""

queryStr_0 = """
{
result: acClassificationPage {
  	id
  	student {
    	id
    	email
    	fullname
    	name
    	surname
  	}
  	semester {
    	id
    	subject {
      	id
      	name
      	program {
        	id
        	name
      	}
    	}
  	}
  	level {
    	id
    	name
  	}
  }

}

"""
