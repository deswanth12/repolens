from mycli.processor import process_data

def test_process_data():
    assert process_data(" Hello ") == "Processed: hello"
