all: cert-admin.p12 cert-cluster.p12

clean:
	rm *.pem
	rm *.csr
	rm *.p12

# Client
cert-admin.p12: cert-admin.crt
	openssl pkcs12 -export \
		-password pass:changeit \
		-in cert-admin.crt -inkey cert-admin-key.pem -out $@

cert-admin.crt: cert-admin.pem ca-intermediate.pem ca-root.pem
	cat $^ > $@

cert-admin.pem: cert-admin.csr ca-intermediate.pem
	cfssl sign -config configs/config.json -profile cert-admin \
		-ca ca-intermediate.pem -ca-key ca-intermediate-key.pem \
		cert-admin.csr configs/cert-admin.json | cfssljson -bare cert-admin

cert-admin.csr:
	cfssl genkey configs/cert-admin.json | cfssljson -bare cert-admin


# Cluster
cert-cluster.p12: cert-cluster.crt
	openssl pkcs12 -export \
		-password pass:changeit \
		-in cert-cluster.crt -inkey cert-cluster-key.pem -out $@

cert-cluster.crt: cert-cluster.pem ca-intermediate.pem ca-root.pem
	cat $^ > $@

cert-cluster.pem: cert-cluster.csr ca-intermediate.pem
	cfssl sign -config configs/config.json -profile cert-cluster \
		-ca ca-intermediate.pem -ca-key ca-intermediate-key.pem \
		cert-cluster.csr configs/cert-cluster.json | cfssljson -bare cert-cluster

cert-cluster.csr:
	cfssl genkey configs/cert-cluster.json | cfssljson -bare cert-cluster

# CAs

ca-intermediate.pem: ca-intermediate.csr ca-root.pem
	cfssl sign -config configs/config.json -profile ca-intermediate \
		-ca ca-root.pem -ca-key ca-root-key.pem \
		ca-intermediate.csr configs/ca-intermediate.json | cfssljson -bare ca-intermediate

ca-intermediate.csr: ca-root.pem configs/ca-intermediate.json
	cfssl genkey configs/ca-intermediate.json | cfssljson -bare ca-intermediate

ca-root.pem: configs/ca-root.json
	cfssl genkey -initca configs/ca-root.json | cfssljson -bare ca-root




