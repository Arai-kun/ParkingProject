# ParkingProject
いつもナビのサイトから任意の駐車場に対していくつかの周辺駐車場の距離と料金を取得するAPIです.</br>
身内の仕事でこんなの欲しいということで作りました.</br>
APIといっても裏ではスクレイピングしてるだけなので、レスポンスがめちゃ遅いです.</br>
なので, どこでも使えるRESTまがいなスクレイピング的な感覚で使うといいと思います.</br>
## URI
一応、以下でAPIを叩けるようにしています.</br>
http://34.71.32.140:3000/search/<任意の駐車場名>
## 開発者向け
ChromeとChromeDriver, Selenium, Flask(暫定的APIサーバ用)を各環境に合わせてインストールすれば動きます.
