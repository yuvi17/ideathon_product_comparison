from flask import Flask
from flask import request
from flask import json,jsonify, json_available
import requests
import pandas as pd
import sqlite3
from flask_cors import CORS


# init code
df = open("/Users/yuvraj/Downloads/IN/IN.txt").read().rstrip().split("\n")
cityInfo= {}
for d in df:
    if(len(d) > 0):
        d = d.split("\t")
        cityInfo[d[1]] = {}
        cityInfo[d[1]]['city'] = d[5]
        cityInfo[d[1]]['state'] = d[3]
        cityInfo[d[1]]['area'] = d[2]
        cityInfo[d[1]]['lat'] = d[-3]
        cityInfo[d[1]]['lon'] = d[-2]

#db seed

conn = sqlite3.connect('ideathon_mma.db')
conn.execute("drop table if exists stores")
conn.execute("drop table if exists products")
conn.execute("drop table if exists store_product_map")
conn.execute("create table stores (id int,name text,address text,city text,state text,pin int)")
conn.execute("create table products (id int,name text,price int ,unit text,description text)")
conn.execute("create table store_product_map (id int,store_id int, product_id int)")

stores = open("/Users/yuvraj/Development/Hackathons/ideathon_mma/product_comparison/stores.csv").read().rstrip().split("\n")
products = open("/Users/yuvraj/Development/Hackathons/ideathon_mma/product_comparison/products.csv").read().rstrip().split("\n")
inv = open("/Users/yuvraj/Development/Hackathons/ideathon_mma/product_comparison/store_inventory.csv").read().rstrip().split("\n")

stores = [tuple(store.split(",")) for store in stores]
inv = [tuple(inventory.split(",")) for inventory in inv]
products = [tuple(product.split(",")) for product in products]

conn.executemany("insert into stores values (?,?,?,?,?,?)",stores)
conn.executemany("insert into products values (?,?,?,?,?)",products)
conn.executemany("insert into store_product_map values (?,?,?)",inv)

conn.commit()



def grofers(product,cityInfo):
    payload = {
        'lat' : cityInfo['lat'],
        'lon' : cityInfo['lon'],
        'q' : "Tata Sampann " + product,
        'start' : 0,
        'size' : 5
    }
    headers = {
        'auth_key': "6d7aa42b20b9e9cd73b0d58d2b91eabb19a960b8ec24d26f51f8360d3aeb9931",
        'referer': "https://grofers.com/s/?q=tata+sampann+rice&suggestion_type=0&t=1",
        'Accept-Encoding': "gzip",
        'Accept-language': "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
        'app_client': "consumer_web",
        'Content-Type': "application/json",
        'Cache-Control': "no-cache",
    }
    r = requests.get("https://grofers.com/v5/search/merchants/26015/products/", headers = headers, params = payload)
    r = r.json()
    print(r.keys())
    response = {}
    response['category'] = 'Grofers'
    items = []
    for product in r['products']:
        item = {}
        url = product['name'].replace("\\","").replace("/","").replace(" ","_").lower()
        item['name'] = product['name']
        item['cost'] = product['price']
        item['unit'] = product['unit']
        item['image_url'] = product['image_url']
        item['purchase_link'] = "https://grofers.com/prn/" + url + "/prid/" + str(product['default_product_id'])
        items.append(item)
    response['items'] = items
    return response


def bigBasket(product):
    slug = "tata sampann " + product
    payload = {
        "slug" : slug,
        "type" : "deck"
    }
    r = requests.get("https://www.bigbasket.com/custompage/getsearchdata/?slug=tata%20sampann%20masala&type=deck")
    r = r.json()

    response = {}
    response['category'] = "Big Basket"
    items = []
    products = r['json_data']['tab_info'][0]['product_info']['products']
    for product in products:
        item = {}
        item['name'] = product['pc_n'] + product['p_desc']
        item['cost'] = product['sp']
        item['unit'] = product['w']
        item['purchase_url'] = 'https://www.bigbasket.com/pd/' + str(product['sku'])
        item['image_url'] = product['p_img_url']
        items.append(item)
    if(len(items) > 5):
        response['items'] = items[0:5]
    else:
        response['items'] = items
    return response



def getProducts(search_val):
    conn = sqlite3.connect('ideathon_mma.db')
    query = "SELECT * FROM store_product_map map join stores s, products p "
    query = query + " on s.id = map.store_id and p.id = map.product_id"
    query = query + " where p.name like ? limit 5"
    response = {}
    param = ("%" + search_val + "%",)
    items = []
    for row in conn.execute(query,param):
        item = {}
        item['name'] = row[10]
        item['price'] = row[11]
        item['store_name'] = row[4]
        item['store_address'] = " ".join(row[5:8])
        items.append(item)
    conn.close()
    response['category'] = "distributors"
    response['items'] = items
    return response


def getProductDescription(product):
    conn = sqlite3.connect('ideathon_mma.db')
    query = "SELECT * FROM products where name like ? limit 1"
    param = ("%" + product + "%",)
    item = {}
    for row in conn.execute(query,param):

        item['name'] = row[1]
        item['price'] = row[2]
        item['unit'] = row[3]
        item['descritption'] = row[4]
    conn.close()
    return item


def getAllProducts(search_term,pincode):
    city = cityInfo[str(pincode)]
    resp = []
    resp.append(grofers(search_term,city))
    resp.append(bigBasket(search_term))
    resp.append(getProducts(search_term))
    return resp

app = Flask(__name__)
CORS(app)

@app.route('/comparison')
def product_comparsion():
    search_term = request.args.get('q')
    pincode = request.args.get('pincode')
    return jsonify(getAllProducts(search_term,pincode))

@app.route('/product_info')
def product_info():
    search_term = request.args.get('q')
    return jsonify(getProductDescription(search_term))

if __name__ == '__main__':
    app.run(debug=True)
