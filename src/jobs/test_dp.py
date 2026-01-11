from pyspark.sql import SparkSession

def run():
    # 1. Start Spark
    spark = SparkSession.builder.appName("KS1-HelloWorld").getOrCreate()
    
    # 2. Do some "Big Data" processing (Create a DataFrame)
    data = [("Aparup", 31), ("KS-1", 1), ("Google", 25)]
    columns = ["Name", "Age"]
    df = spark.createDataFrame(data, columns)
    
    # 3. Show results
    print("⚡ Kinetic Spark says Hello World! ⚡")
    df.show()
    
    # 4. Stop
    spark.stop()

if __name__ == "__main__":
    run()